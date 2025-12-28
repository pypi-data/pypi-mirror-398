# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Smart Command Triage Engine

Provides intelligent classification of shell commands to optimize execution:
- TRIVIAL: Instant execution, no LLM, no confirmation (echo, pwd, date)
- SAFE: Instant execution, no LLM, no confirmation (cat, ls, head)
- RISKY: Optional LLM, single confirmation (cp, mv, mkdir)
- DESTRUCTIVE: Always LLM, double confirmation (rm, sudo, chmod)
- UNKNOWN: Fallback to LLM analysis
"""


from enum import Enum
import re
from typing import Optional, Tuple, Dict, Any, List
import time
import subprocess


class CommandSafety(Enum):
    """Command safety classification levels"""
    TRIVIAL = "trivial"          # Instant execution, no confirmation
    SAFE = "safe"               # Instant execution, no confirmation
    RISKY = "risky"             # Single confirmation
    DESTRUCTIVE = "destructive"  # Double confirmation
    UNKNOWN = "unknown"         # Fallback to LLM


class TriageResult:
    """Result of command triage analysis"""

    def __init__(self, safety: CommandSafety, command: Optional[str] = None,
                 confidence: float = 1.0, reasoning: str = "", bypass_llm: Optional[bool] = None):
        self.safety = safety
        self.command = command
        self.confidence = confidence
        self.reasoning = reasoning
        # If bypass_llm explicitly set, use it; otherwise determine from safety
        # This allows regex fallback to bypass LLM even for DESTRUCTIVE commands when it has generated a command
        if bypass_llm is not None:
            self.bypass_llm = bypass_llm
        else:
            self.bypass_llm = safety in [CommandSafety.TRIVIAL, CommandSafety.SAFE]
        self.confirmation_required = safety in [CommandSafety.RISKY, CommandSafety.DESTRUCTIVE]

    def __repr__(self):
        return f"TriageResult(safety={self.safety.value}, command='{self.command}', bypass_llm={self.bypass_llm})"


class SmartCommandTriage:
    """Smart command triage engine for efficient shell command processing"""

    def __init__(self):
        self.trivial_patterns = self._compile_patterns(self._get_trivial_patterns())
        self.safe_patterns = self._compile_patterns(self._get_safe_patterns())
        self.risky_patterns = self._compile_patterns(self._get_risky_patterns())
        self.destructive_patterns = self._compile_patterns(self._get_destructive_patterns())

    def _get_trivial_patterns(self) -> Dict[str, str]:
        """Patterns for trivial commands that can execute instantly"""
        return {
            # Print/Echo operations
            r"^(print|echo)\s+(.+)$": "echo {1}",
            r"^say\s+(.+)$": "echo {0}",

            # Basic info commands
            r"^(pwd|current directory|where am i)$": "pwd",
            r"^(whoami|who am i|current user)$": "whoami",
            r"^(date|current time|what time)$": "date",
            r"^(hostname|computer name)$": "hostname",

            # Simple listing
            r"^(ls|list files?)$": "ls",
            r"^(ls -la?|list all files?|show all files?)$": "ls -la",

            # Environment info
            r"^(env|environment|show env)$": "env",
            r"^(path|show path)$": "echo $PATH",

            # Help commands
            r"^help\s+(.+)$": "man {0} 2>/dev/null || {0} --help 2>/dev/null || echo 'No help available for {0}'",
        }

    def _get_safe_patterns(self) -> Dict[str, str]:
        """Patterns for safe read-only commands"""
        return {
            # File viewing (read-only)
            r"^(cat|show|display)\s+([\w\-./]+\.(?:txt|md|log|json|yaml|yml|py|js|html|css))$": "cat {1}",
            r"^head\s+([\w\-./]+)$": "head {0}",
            r"^tail\s+([\w\-./]+)$": "tail {0}",
            r"^(less|more)\s+([\w\-./]+)$": "{0} {1}",

            # Directory operations (read-only)
            r"^ls\s+([\w\-./~]+)$": "ls {0}",
            r"^ls -la?\s+([\w\-./~]+)$": "ls -la {0}",
            r"^(tree)\s+([\w\-./~]+)$": "tree {0} || find {0} -type d | head -20",

            # File information
            r"^(wc|word count)\s+([\w\-./]+)$": "wc {1}",
            r"^(file type|file)\s+([\w\-./]+)$": "file {1}",
            r"^(stat|file stats?)\s+([\w\-./]+)$": "stat {1}",

            # Process info (read-only)
            r"^(ps|processes)$": "ps aux",
            r"^(jobs|background jobs)$": "jobs",

            # System info (read-only)
            r"^(df|disk space|disk usage)$": "df -h",
            r"^(du|directory size)\s+([\w\-./~]+)$": "du -sh {1}",
            r"^(uptime|system uptime)$": "uptime",
            r"^(free|memory usage|memory)$": "free -h 2>/dev/null || vm_stat",

            # File finding and sorting (read-only)
            r"^show me the (?:top )?(\d+) largest files? in (\w+) folder$": "find ~/{1} -type f -exec du -h {{}} + | sort -rh | head -n {0}",
            r"^find (?:the )?largest files? in (\w+)$": "find ~/{0} -type f -exec du -h {{}} + | sort -rh | head -10",
            r"^(?:show|list) largest files? in ([\w\-./~]+)$": "find {0} -type f -exec du -h {{}} + | sort -rh | head -10",

            # Network info (safe)
            r"^(ping)\s+([\w\-.]+)$": "ping -c 4 {1}",
            r"^(nslookup|dns)\s+([\w\-.]+)$": "nslookup {1}",
        }

    def _get_risky_patterns(self) -> Dict[str, str]:
        """Patterns for risky commands that need confirmation"""
        return {
            # File operations
            r"^(cp|copy)\s+(.+)\s+(.+)$": "cp {1} {2}",
            r"^(mv|move|rename)\s+(.+)\s+(.+)$": "mv {1} {2}",
            r"^(mkdir|create dir(?:ectory)?)\s+(.+)$": "mkdir -p {1}",
            r"^(touch|create file)\s+([\w\-./]+)$": "touch {1}",

            # File editing (can be risky)
            r"^(nano|vim|vi|emacs)\s+([\w\-./]+)$": "{0} {1}",

            # Archive operations
            r"^(tar|archive)\s+(.+)$": None,  # Complex, needs LLM
            r"^(unzip|extract)\s+([\w\-./]+\.zip)$": "unzip {1}",

            # Git operations (can be risky)
            r"^git\s+(status|log|diff|show)": "git {0}",  # Read-only git commands
            r"^git\s+(.+)$": None,  # Other git commands need LLM analysis

            # Process management
            r"^(kill)\s+(\d+)$": "kill {1}",
            r"^(killall)\s+([\w\-]+)$": "killall {1}",

            # Network operations
            r"^(curl|wget)\s+(https?://[\w\-./?&=]+)$": "{0} {1}",
            r"^(ssh)\s+([\w\-@.]+)$": "ssh {1}",
        }

    def _get_destructive_patterns(self) -> Dict[str, str]:
        """Patterns for destructive commands that always need LLM analysis"""
        return {
            # File deletion (always dangerous)
            r"^(rm|delete|remove).*": None,

            # Permission changes
            r"^(chmod|chmod).*": None,
            r"^(chown).*": None,

            # System modifications
            r"^(sudo).*": None,
            r"^(su\s|su$)": None,

            # Service management
            r"^(systemctl|service).*": None,

            # Package management (can be destructive)
            r"^(apt|yum|dnf|brew|pip)\s+(remove|uninstall|purge).*": None,
            r"^(npm|yarn)\s+(uninstall|remove).*": None,

            # Disk operations
            r"^(fdisk|mkfs|mount|umount).*": None,
            r"^(dd).*": None,

            # Network configuration
            r"^(iptables|ufw|firewall).*": None,
        }

    def _compile_patterns(self, pattern_dict: Dict[str, str]) -> List[Tuple[re.Pattern, Optional[str]]]:
        """Compile regex patterns for efficient matching"""
        compiled = []
        for pattern, template in pattern_dict.items():
            try:
                compiled.append((re.compile(pattern, re.IGNORECASE), template))
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern}': {e}")
                continue
        return compiled

    async def triage(self, user_input: str, llm_provider=None) -> TriageResult:
        """Perform smart LLM-first triage on user input"""
        user_input = user_input.strip()

        if not user_input:
            return TriageResult(
                safety=CommandSafety.UNKNOWN,
                reasoning="Empty input"
            )

        # LLM-FIRST APPROACH: Use LLM intelligence for smart triage
        if llm_provider:
            try:
                llm_result = await self._llm_triage(user_input, llm_provider)
                if llm_result:
                    return llm_result
            except Exception as e:
                print(f"🔄 LLM triage failed, falling back to regex: {e}")

        # FALLBACK: Regex patterns for when LLM is unavailable or fails
        return self._regex_triage(user_input)

    async def _llm_triage(self, user_input: str, llm_provider) -> TriageResult:
        """LLM-powered intelligent command triage"""
        triage_prompt = f"""Analyze this shell command request for safety classification and command generation.

Input: "{user_input}"

Classify the safety level and generate the appropriate shell command:

SAFETY LEVELS:
- TRIVIAL: Simple info commands (echo, pwd, date, whoami) - instant execution, no confirmation
- SAFE: Read-only operations (cat, ls, head, ping) - instant execution, no confirmation
- RISKY: File operations that modify (cp, mv, mkdir) - single confirmation required
- DESTRUCTIVE: Dangerous operations (rm, sudo, chmod) - requires careful analysis
- UNKNOWN: Complex requests needing human review

TASK: Respond with JSON in this exact format:
{{
    "safety": "trivial|safe|risky|destructive|unknown",
    "command": "actual shell command to execute (null if destructive/unknown)",
    "confidence": 0.95,
    "reasoning": "Brief explanation of classification decision"
}}

Focus on practical shell command generation and accurate safety assessment."""

        try:
            from pydantic import BaseModel
            from typing import Optional

            class TriageResponse(BaseModel):
                safety: str
                command: Optional[str]
                confidence: float
                reasoning: str

            # Use LLM to analyze and classify the command
            import json
            full_prompt = f"You are an expert shell command safety analyzer. Respond only with valid JSON.\n\n{triage_prompt}"
            response_text = await llm_provider.complete(full_prompt)

            # Parse JSON response
            response_data = json.loads(response_text)
            response = TriageResponse(**response_data)

            # Parse LLM response
            safety_map = {
                "trivial": CommandSafety.TRIVIAL,
                "safe": CommandSafety.SAFE,
                "risky": CommandSafety.RISKY,
                "destructive": CommandSafety.DESTRUCTIVE,
                "unknown": CommandSafety.UNKNOWN
            }

            safety = safety_map.get(response.safety.lower(), CommandSafety.UNKNOWN)

            return TriageResult(
                safety=safety,
                command=response.command,
                confidence=min(max(response.confidence, 0.0), 1.0),
                reasoning=f"LLM Analysis: {response.reasoning}"
            )

        except Exception as e:
            # LLM failed, will fall back to regex
            raise Exception(f"LLM triage analysis failed: {e}")

    def _regex_triage(self, user_input: str) -> TriageResult:
        """Fallback regex-based triage when LLM is unavailable"""

        # Quick regex patterns for COMMON cases only (not exhaustive)

        # 1. DESTRUCTIVE (highest priority for safety)
        # Extract command from natural language (simple heuristic)
        command = user_input  # Default to raw input

        # Try to extract just the command part
        # e.g., "remove the file /tmp/test.txt" → "rm /tmp/test.txt"
        if user_input.lower().startswith(('remove', 'delete')):
            # Extract the file path (re is already imported at top of file)
            file_match = re.search(r'/[\w/.]+', user_input)
            if file_match:
                command = f"rm {file_match.group()}"
        elif user_input.lower().startswith('list'):
            command = "ls -la"

        destructive_keywords = ['rm ', 'sudo ', 'chmod ', 'chown ', 'dd ', 'mkfs']
        if any(keyword in command.lower() for keyword in destructive_keywords):
            return TriageResult(
                safety=CommandSafety.DESTRUCTIVE,
                command=command,  # Include generated command
                reasoning="Potentially destructive operation detected (regex fallback)",
                bypass_llm=True  # v0.4.13: Bypass LLM since we have the command - direct path will show confirmation
            )

        # 2. TRIVIAL (most common optimization target)
        trivial_patterns = {
            r"^(echo|print)\s+(.+)$": "echo {1}",
            r"^(pwd|whoami|date|hostname)$": "{0}",
            r"^(ls|list files?)$": "ls",
        }

        for pattern, template in trivial_patterns.items():
            match = re.match(pattern, user_input, re.IGNORECASE)
            if match:
                try:
                    command = template.format(*match.groups()) if match.groups() else template.format(match.group(0))
                    return TriageResult(
                        safety=CommandSafety.TRIVIAL,
                        command=command,
                        confidence=0.9,
                        reasoning="Common trivial pattern matched (regex fallback)"
                    )
                except:
                    pass

        # 3. SAFE (read-only operations)
        safe_keywords = ['cat ', 'head ', 'tail ', 'less ', 'more ', 'find ', 'grep ', 'ping ']
        if any(keyword in user_input.lower() for keyword in safe_keywords):
            return TriageResult(
                safety=CommandSafety.SAFE,
                reasoning="Read-only operation detected (regex fallback)"
            )

        # 4. Default: UNKNOWN (let LLM handle or require human review)
        return TriageResult(
            safety=CommandSafety.UNKNOWN,
            reasoning="Complex command - requires LLM analysis (regex fallback insufficient)"
        )

    def _apply_template(self, template: str, groups: tuple) -> str:
        """Apply regex groups to command template"""
        try:
            # Handle both indexed ({0}, {1}) and named formatting
            if '{0}' in template or '{1}' in template:
                return template.format(*groups)
            else:
                # Legacy numbered formatting
                for i, group in enumerate(groups):
                    template = template.replace(f'{{{i}}}', group)
                return template
        except (IndexError, KeyError, ValueError) as e:
            # If template formatting fails, return a safe fallback
            raise ValueError(f"Template application failed: {e}")

    async def execute_direct(self, triage_result: TriageResult, timeout: int = 10) -> Dict[str, Any]:
        """Execute a triaged command directly"""

        if not triage_result.command:
            raise ValueError("No command to execute")

        if triage_result.confirmation_required:
            raise ValueError("Command requires confirmation - cannot execute directly")

        start_time = time.time()

        try:
            # Execute command with timeout
            result = subprocess.run(
                triage_result.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            execution_time = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "command": triage_result.command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "execution_time": execution_time,
                "safety": triage_result.safety.value,
                "reasoning": triage_result.reasoning,
                "bypassed_llm": True
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "command": triage_result.command,
                "error": f"Command timed out after {timeout}s",
                "execution_time": time.time() - start_time,
                "safety": triage_result.safety.value
            }
        except Exception as e:
            return {
                "success": False,
                "command": triage_result.command,
                "error": f"Execution error: {str(e)}",
                "execution_time": time.time() - start_time,
                "safety": triage_result.safety.value
            }

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about loaded patterns"""
        return {
            "trivial_patterns": len(self.trivial_patterns),
            "safe_patterns": len(self.safe_patterns),
            "risky_patterns": len(self.risky_patterns),
            "destructive_patterns": len(self.destructive_patterns),
            "total_patterns": (
                len(self.trivial_patterns) +
                len(self.safe_patterns) +
                len(self.risky_patterns) +
                len(self.destructive_patterns)
            )
        }

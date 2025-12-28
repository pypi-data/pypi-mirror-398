# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Safety Analyzer - Enhanced command safety intelligence using ExplainCommandFunction

Provides deep safety analysis for shell commands:
- Integrates with ExplainCommandFunction for detailed command analysis
- Generates safety warnings with risk assessment
- Suggests safer alternatives
- Enhances confirmation prompts with educational context
"""


import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class SafetyLevel(Enum):
    """Safety levels aligned with ExplainCommandFunction"""
    SAFE = "safe"
    CAUTION = "caution"
    DANGEROUS = "dangerous"
    UNKNOWN = "unknown"


@dataclass
class SafetyAnalysis:
    """Result of safety analysis"""
    level: SafetyLevel
    summary: str
    risks: List[str]
    recommendations: List[str]
    alternatives: List[str]
    breakdown: List[Dict[str, str]]
    example_output: str = ""
    confidence: float = 0.0

    def format_warning(self) -> str:
        """Format safety analysis as a warning message"""
        lines = []

        # Safety header with emoji
        if self.level == SafetyLevel.DANGEROUS:
            lines.append("🚨 WARNING: DANGEROUS COMMAND")
        elif self.level == SafetyLevel.CAUTION:
            lines.append("⚠️  CAUTION: This command requires care")
        elif self.level == SafetyLevel.SAFE:
            lines.append("✅ Safe command")
        else:
            lines.append("❓ Unknown safety level")

        lines.append("")

        # Summary
        lines.append(f"📝 {self.summary}")
        lines.append("")

        # Breakdown
        if self.breakdown:
            lines.append("🔍 What this does:")
            for i, part in enumerate(self.breakdown, 1):
                syntax = part.get("syntax", "")
                description = part.get("description", "")
                lines.append(f"  {i}. `{syntax}` → {description}")
            lines.append("")

        # Risks
        if self.risks:
            lines.append(f"{'⚠️' if self.level == SafetyLevel.CAUTION else '🚨'} Potential Risks:")
            for risk in self.risks:
                lines.append(f"  • {risk}")
            lines.append("")

        # Recommendations
        if self.recommendations:
            lines.append("💡 Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")

        # Alternatives
        if self.alternatives:
            lines.append("🔄 Safer Alternatives:")
            for alt in self.alternatives:
                lines.append(f"  • {alt}")
            lines.append("")

        return "\n".join(lines)

    def should_block(self) -> bool:
        """Determine if command should be blocked entirely"""
        return self.level == SafetyLevel.DANGEROUS and any(
            keyword in risk.lower()
            for risk in self.risks
            for keyword in ["destroy", "unrecoverable", "all files", "system"]
        )


class SafetyAnalyzer:
    """Enhanced safety analyzer using ExplainCommandFunction"""

    def __init__(self):
        """Initialize safety analyzer"""
        self._explain_function = None

    async def analyze_command(
        self,
        command: str,
        llm_provider: Any,
        detail_level: str = "detailed"
    ) -> Optional[SafetyAnalysis]:
        """
        Analyze command safety using ExplainCommandFunction.

        Args:
            command: Shell command to analyze
            llm_provider: LLM provider for analysis
            detail_level: Level of detail (basic/detailed/expert)

        Returns:
            SafetyAnalysis with risk assessment and recommendations
        """
        if not command or not llm_provider:
            return None

        try:
            # Lazy import to avoid circular dependency
            if not self._explain_function:
                from ...functions.shell.explain_command_function import ExplainCommandFunction
                self._explain_function = ExplainCommandFunction()

            # Create minimal execution context
            from ...core.models import ExecutionContext
            context = ExecutionContext(
                chat_context=None,
                user_input=f"explain command: {command}",
                function_name="explain_command",
                parameters={"command": command, "detail_level": detail_level},
                llm_provider=llm_provider
            )

            # Execute analysis
            result = await self._explain_function.execute(
                {"command": command, "detail_level": detail_level},
                context
            )

            if not result.success or "explanation" not in result.data:
                return None

            # Parse explanation
            explanation = result.data["explanation"]
            safety_data = explanation.get("safety", {})

            # Convert to SafetyAnalysis
            return SafetyAnalysis(
                level=SafetyLevel(safety_data.get("level", "unknown")),
                summary=explanation.get("summary", ""),
                risks=safety_data.get("risks", []),
                recommendations=safety_data.get("recommendations", []),
                alternatives=explanation.get("alternatives", []),
                breakdown=explanation.get("breakdown", []),
                example_output=explanation.get("example_output", ""),
                confidence=result.data.get("confidence", 0.0)
            )

        except Exception as e:
            # Graceful fallback
            import os
            if os.getenv('AII_DEBUG'):
                print(f"🔍 DEBUG: Safety analysis failed: {e}")
            return None

    async def get_confirmation_prompt(
        self,
        command: str,
        analysis: Optional[SafetyAnalysis] = None
    ) -> str:
        """
        Generate enhanced confirmation prompt with safety analysis.

        Args:
            command: Command to execute
            analysis: Optional safety analysis result

        Returns:
            Formatted confirmation prompt
        """
        lines = []

        if analysis:
            # Show full safety analysis
            lines.append(analysis.format_warning())
            lines.append("─" * 60)
            lines.append("")

        # Command to execute
        lines.append(f"Command to execute: `{command}`")
        lines.append("")

        # Confirmation question
        if analysis and analysis.level == SafetyLevel.DANGEROUS:
            lines.append("⚠️  Are you ABSOLUTELY SURE you want to run this? (yes/no)")
            lines.append("   Type 'yes' to confirm, anything else to cancel:")
        else:
            lines.append("Execute this command? (y/n):")

        return "\n".join(lines)

    def is_dangerous_pattern(self, command: str) -> bool:
        """
        Fast heuristic check for dangerous patterns.
        Used for immediate warning before LLM analysis.

        Args:
            command: Command to check

        Returns:
            True if command matches dangerous patterns
        """
        # Handle None command (when triage doesn't generate a command)
        if command is None:
            return False

        command_lower = command.lower().strip()

        # Destructive deletion patterns
        dangerous_patterns = [
            # Critical system paths
            r"rm\s+-rf\s+/\s*$",            # rm -rf /
            r"rm\s+-rf\s+/[a-z]+",          # rm -rf /usr, /etc, /bin, etc.
            r"rm\s+-rf\s+\*",               # rm -rf *
            r"rm\s+-rf\s+\.\s*/\*",         # rm -rf ./*
            r"rm\s+-rf\s+~",                # rm -rf ~

            # Any rm -rf should get analysis (catch-all for safety)
            r"rm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\s+",  # rm -rf or rm -fr with any path

            # Dangerous system commands
            r":\(\)\{.*;\};:",              # Fork bomb
            r"dd\s+if=.*of=/dev/",          # dd to device
            r"mkfs",                        # Format filesystem
            r">\s*/dev/sd",                 # Write to disk device

            # Dangerous permissions
            r"chmod\s+(-r|--recursive)\s+777",  # Recursive 777
            r"chown\s+-r.*root",            # Change ownership to root

            # Sudo with destructive commands
            r"sudo\s+rm\s+-rf",             # sudo rm -rf
        ]

        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, command_lower):
                return True

        return False

    async def suggest_alternatives(
        self,
        command: str,
        llm_provider: Any
    ) -> List[str]:
        """
        Suggest safer alternatives for a command.

        Args:
            command: Original command
            llm_provider: LLM provider for suggestions

        Returns:
            List of safer alternative commands
        """
        analysis = await self.analyze_command(command, llm_provider)
        if analysis and analysis.alternatives:
            return analysis.alternatives

        # Fallback heuristics for common dangerous commands
        if "rm -rf" in command:
            return [
                "rm -i <file>  # Interactive deletion with confirmation",
                "trash <file>  # Move to trash instead of permanent delete",
                "rm -rf <specific-directory>  # Use specific path, not wildcards"
            ]
        elif "chmod 777" in command:
            return [
                "chmod 755 <file>  # Owner full access, others read-execute",
                "chmod 644 <file>  # Owner read-write, others read-only",
                "Use specific permissions instead of 777"
            ]
        elif "sudo" in command:
            return [
                "Check if sudo is really needed",
                "Use specific sudo commands, not 'sudo su'",
                "Verify the command before running with elevated privileges"
            ]

        return []

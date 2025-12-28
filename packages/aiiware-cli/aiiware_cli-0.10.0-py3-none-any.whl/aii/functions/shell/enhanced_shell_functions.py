# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Enhanced Shell Command Functions with LLM-based Generation"""


import asyncio
import os
import platform
import re
import time
from datetime import datetime
from typing import Any

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)


class EnhancedShellCommandFunction(FunctionPlugin):
    """Enhanced shell command function with LLM-based generation and token tracking"""

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "shell_command"

    @property
    def description(self) -> str:
        return """Generate and execute shell commands based on natural language requests.

Use this function when the user wants to RUN a shell operation (list, find, search, create, delete, etc.).

Common patterns:
- "list [type] files in [location]"
- "find [files/folders] [criteria]"
- "search for [pattern] in [files]"
- "show [information]"
- "delete/remove [files]"
- "create/make [files/directories]"
- "count [items]"

The 'request' parameter should contain the natural language description of what to do.

Examples:
- "list all Python files in current directory" → request: "list all Python files in current directory"
- "find the top 5 largest files in Downloads" → request: "find the top 5 largest files in Downloads"
- "count lines in all .py files" → request: "count lines in all .py files"
- "show disk usage" → request: "show disk usage"

Output: Generated shell command with explanation and confirmation prompt for execution."""

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "request": ParameterSchema(
                name="request",
                type="string",
                required=True,
                description="Natural language description of what shell command to run",
            ),
            "execute": ParameterSchema(
                name="execute",
                type="boolean",
                required=False,
                default=True,  # v0.4.13: Default to True - users expect execution
                description="Whether to execute the command after generation (requires confirmation for risky commands)",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        # Dynamic confirmation based on command safety
        return False  # We'll handle confirmation logic in execute()

    @property
    def safety_level(self) -> FunctionSafety:
        # Dynamic safety level based on triage
        return FunctionSafety.CONTEXT_DEPENDENT

    @property
    def default_output_mode(self) -> "OutputMode":
        """Default output mode: standard mode to show command + result with metrics"""
        from ...core.models import OutputMode
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list["OutputMode"]:
        """Supports all output modes"""
        from ...core.models import OutputMode
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(self, context: ExecutionContext) -> ValidationResult:
        """Check prerequisites - LLM is required for shell command generation"""
        # v0.6.0: Always require LLM for consistent token tracking
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                message="LLM provider required for shell command generation"
            )
        return ValidationResult(valid=True)

    async def execute(self, parameters: dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """Execute shell command generation using LLM"""

        request = parameters["request"]
        execute_command = parameters.get("execute", True)  # v0.4.13: Default to True - users expect execution
        start_time = time.time()

        try:
            # v0.6.0: Always use LLM path for consistent token tracking
            # Triage system removed for simplicity
            if not context.llm_provider:
                return ExecutionResult(
                    success=False,
                    message="LLM provider required for shell command generation"
                )

            # Always use LLM path
            return await self._execute_llm_only_path(request, execute_command, context, start_time)

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"❌ ERROR in EnhancedShellCommandFunction.execute:\n{error_details}")
            return ExecutionResult(
                success=False,
                message=f"Command processing failed: {str(e)}\n{error_details}"
            )

    async def _execute_llm_only_path(self, request: str, execute_command: bool, context: ExecutionContext, start_time: float) -> ExecutionResult:
        """LLM-only path for shell command generation with proper token tracking"""

        try:
            # Get system info
            system_info = self._get_system_info()

            # Build prompt for command generation
            prompt = self._build_llm_prompt(request, system_info)

            # Call LLM and track token usage
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                response_content = llm_response.content
                usage = llm_response.usage or {}
            else:
                response_content = await context.llm_provider.complete(prompt)
                usage = {}

            # Parse command from response
            parsed = self._parse_command_response(response_content)
            if not parsed:
                return ExecutionResult(
                    success=False,
                    message="Failed to generate a valid shell command"
                )

            command = parsed["command"]
            explanation = parsed.get("explanation", "")

            # Always require confirmation for execution (v0.6.0)
            if execute_command:
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": explanation,
                        "requires_execution_confirmation": True,
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    }
                )
            else:
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": explanation,
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    }
                )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Command generation failed: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"}
            )

    def _build_llm_prompt(self, request: str, system_info: dict[str, str]) -> str:
        """Build simplified prompt for shell command generation"""

        return f"""You are an expert system administrator. Generate a shell command based on the user's natural language request.

System Information:
- OS: {system_info['os']}
- Shell: {system_info['shell']}
- Platform: {system_info['platform']}
- Home Directory: {system_info['home_dir']}
- Current Directory: {system_info['current_dir']}

User Request: "{request}"

Generate the actual shell command that accomplishes the user's request. Consider:
1. Use appropriate commands for the detected OS/shell
2. Generate the ACTUAL command (not a checking/preview script)
3. Use human-readable output when possible
4. Handle edge cases (empty results, permissions, etc.)
5. Prefer portable commands when possible

IMPORTANT: Generate the ACTUAL command the user wants to run. The system will handle confirmation prompts - don't generate "checking" or "preview" scripts.

Examples:
- User: "remove file.txt" → `rm -i file.txt` (actual deletion, not echo/checking)
- User: "delete all logs" → `rm -i *.log` (actual deletion)
- User: "list files" → `ls -la` (listing is safe)

Respond with JSON in this format:
{{
  "command": "the actual shell command",
  "explanation": "clear explanation of what the command does",
  "safety_notes": ["list of safety considerations or warnings"],
  "confidence": 85.0,
  "reasoning": "why this command was chosen"
}}

If the request is ambiguous, choose the most reasonable interpretation."""

    async def _execute_direct_path(self, triage_result, request: str, execute_command: bool, start_time: float, context: ExecutionContext = None) -> ExecutionResult:
        """Direct execution path for trivial/safe commands with optional safety analysis"""

        command = triage_result.command

        # Check for dangerous patterns even in "safe" commands
        if execute_command and self.safety_analyzer.is_dangerous_pattern(command):
            # Fast dangerous pattern detected - get detailed analysis
            if context and context.llm_provider:
                analysis = await self.safety_analyzer.analyze_command(
                    command,
                    context.llm_provider
                )

                if analysis and analysis.level.value == "dangerous":
                    # Show warning and require explicit confirmation
                    confirmation_prompt = await self.safety_analyzer.get_confirmation_prompt(
                        command,
                        analysis
                    )

                    return ExecutionResult(
                        success=True,
                        message=confirmation_prompt,
                        data={
                            "command": command,
                            "safety_analysis": {
                                "level": analysis.level.value,
                                "summary": analysis.summary,
                                "risks": analysis.risks,
                                "recommendations": analysis.recommendations,
                                "alternatives": analysis.alternatives,
                            },
                            "requires_execution_confirmation": True,
                            "confirmation_type": "explicit",  # Requires "yes" not just "y"
                            "clean_output": command,
                        }
                    )

        if os.getenv("AII_DEBUG"):
            print(f"🔍 DEBUG: Checking execution path - execute_command={execute_command}, confirmation_required={triage_result.confirmation_required}, safety={triage_result.safety}")

        # IMPORTANT: v0.6.0 - ALWAYS require client-side confirmation for ALL shell commands
        # Never auto-execute, even for "safe" commands - let user decide
        if True:  # Always require confirmation
            # Show command with confirmation prompt if execution is requested
            processing_time = time.time() - start_time

            # Generate risks based on safety level
            risks = []
            if triage_result.safety == CommandSafety.DESTRUCTIVE:
                risks = ["DESTRUCTIVE operation - may delete data or modify system files"]
            elif triage_result.safety == CommandSafety.RISKY:
                risks = ["May modify files or system state", "Review command carefully before execution"]
            elif triage_result.safety == CommandSafety.SAFE:
                risks = ["Read-only operation - safe to execute"]
            elif triage_result.safety == CommandSafety.TRIVIAL:
                risks = ["Basic command with no side effects"]

            # Debug logging
            if os.getenv("AII_DEBUG"):
                print(f"🔍 DEBUG: Direct path - execute_command={execute_command}, risks={risks}")

            # ALWAYS require confirmation when user wants to execute
            if execute_command:
                if os.getenv("AII_DEBUG"):
                    print(f"🔍 DEBUG: Returning confirmation prompt for command: {command}")
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{triage_result.reasoning}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": triage_result.reasoning,
                        "risks": risks,  # IMPORTANT: Include risks for client display
                        "safety": triage_result.safety.value,
                        "bypassed_llm": True,
                        "tokens_saved": "~300-500",
                        "time_saved": f"~{14-processing_time:.1f}s",
                        "processing_time": processing_time,
                        "requires_execution_confirmation": True,  # ALWAYS true
                        "triage_enabled": True
                    }
                )
            else:
                # Just show the generated command (no execution requested)
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{triage_result.reasoning}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": triage_result.reasoning,
                        "risks": risks,  # Include risks even when not executing
                        "safety": triage_result.safety.value,
                        "bypassed_llm": True,
                        "tokens_saved": "~300-500",
                        "time_saved": f"~{14-processing_time:.1f}s",
                        "processing_time": processing_time,
                        "requires_execution_confirmation": False,
                        "triage_enabled": True
                    }
                )

    async def _execute_llm_path(self, triage_result, request: str, execute_command: bool, context: ExecutionContext, start_time: float) -> ExecutionResult:
        """Enhanced LLM path with safety analysis for risky/destructive commands"""

        try:
            # Get system info
            system_info = self._get_system_info()

            # Generate command using LLM
            prompt = self._build_command_generation_prompt(request, system_info, triage_result)

            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(prompt)
                response_content = llm_response.content
                usage = llm_response.usage or {}
            else:
                response_content = await context.llm_provider.complete(prompt)
                usage = {}

            # Parse command from response
            parsed = self._parse_command_response(response_content)
            if not parsed:
                return ExecutionResult(
                    success=False,
                    message="Failed to generate a valid shell command"
                )

            command = parsed["command"]
            explanation = parsed.get("explanation", "")

            # Check for dangerous patterns with safety analysis
            if self.safety_analyzer.is_dangerous_pattern(command):
                # Get detailed safety analysis
                analysis = await self.safety_analyzer.analyze_command(
                    command,
                    context.llm_provider
                )

                if analysis:
                    # Generate enhanced confirmation prompt
                    confirmation_prompt = await self.safety_analyzer.get_confirmation_prompt(
                        command,
                        analysis
                    )

                    return ExecutionResult(
                        success=True,
                        message=confirmation_prompt,
                        data={
                            "command": command,
                            "clean_output": command,
                            "explanation": explanation,
                            "safety_analysis": {
                                "level": analysis.level.value,
                                "summary": analysis.summary,
                                "risks": analysis.risks,
                                "recommendations": analysis.recommendations,
                                "alternatives": analysis.alternatives,
                            },
                            "requires_execution_confirmation": True,
                            "confirmation_type": "explicit" if analysis.level.value == "dangerous" else "standard",
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                            "triage_safety": triage_result.safety.value,
                        }
                    )

            # Standard confirmation for non-dangerous commands
            if execute_command:
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}\n\nExecute this command? (y/n):",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": explanation,
                        "requires_execution_confirmation": True,
                        "input_tokens": usage.get("input_tokens"),
                        "output_tokens": usage.get("output_tokens"),
                        "triage_safety": triage_result.safety.value,
                    }
                )
            else:
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data={
                        "command": command,
                        "clean_output": command,
                        "explanation": explanation,
                        "input_tokens": usage.get("input_tokens"),
                        "output_tokens": usage.get("output_tokens"),
                        "triage_safety": triage_result.safety.value,
                    }
                )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Command generation failed: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"}
            )

    def _build_command_generation_prompt(self, request: str, system_info: dict[str, str], triage_result=None) -> str:
        """Build prompt for shell command generation with safety context"""

        safety_context = ""
        if triage_result:
            safety_context = f"\nSafety Level: {triage_result.safety.value}\n"
            if triage_result.reasoning:
                safety_context += f"Context: {triage_result.reasoning}\n"

        return f"""You are an expert system administrator. Generate a shell command based on the user's natural language request.

System Information:
- OS: {system_info['os']}
- Shell: {system_info['shell']}
- Platform: {system_info['platform']}
- Home Directory: {system_info['home_dir']}
- Current Directory: {system_info['current_dir']}
{safety_context}
User Request: "{request}"

Generate the actual shell command that accomplishes the user's request. Consider:
1. Use appropriate commands for the detected OS/shell
2. Generate the ACTUAL command (not a checking/preview script)
3. Use human-readable output when possible
4. Handle edge cases (empty results, permissions, etc.)
5. Prefer portable commands when possible

IMPORTANT: Generate the ACTUAL command the user wants to run. The system will handle confirmation prompts for dangerous operations - don't generate "checking" or "preview" scripts.

Examples:
- User: "remove file.txt" → `rm -i file.txt` (actual deletion, not echo/checking)
- User: "delete all logs" → `rm -i *.log` (actual deletion)
- User: "list files" → `ls -la` (listing is safe)

Respond with JSON in this format:
{{
  "command": "the actual shell command",
  "explanation": "clear explanation of what the command does",
  "safety_notes": ["list of safety considerations or warnings"],
  "confidence": 85.0,
  "reasoning": "why this command was chosen"
}}

If the request is ambiguous, choose the most reasonable interpretation."""

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute a confirmed shell command"""
        import asyncio
        import os

        try:
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd(),
            )

            stdout, stderr = await process.communicate()

            # Prepare output
            output_lines = []

            if stdout:
                stdout_text = stdout.decode("utf-8").strip()
                if stdout_text:
                    output_lines.append(stdout_text)

            if stderr:
                stderr_text = stderr.decode("utf-8").strip()
                if stderr_text:
                    output_lines.append(f"⚠️  stderr: {stderr_text}")

            output = "\n".join(output_lines) if output_lines else ""
            success = process.returncode == 0

            # Prepare result data
            result_data = {
                "command": command,
                "output": output,
                "return_code": process.returncode,
                "success": success,
                "clean_output": output if output else "Command executed successfully",  # For CLEAN mode
            }

            # Include original tokens if provided
            if original_tokens:
                result_data["input_tokens"] = original_tokens.get("input_tokens")
                result_data["output_tokens"] = original_tokens.get("output_tokens")

            # Format message based on success
            if success:
                # v0.4.13: Don't repeat command (user already saw it in confirmation prompt)
                if output_lines:  # Check if there was actual output
                    message = f"✅ Command executed successfully:\n\n{output}"
                else:
                    message = "✅ Command executed successfully"
            else:
                # On failure, show command for debugging
                message = f"❌ Command failed (exit code {process.returncode}):\n\n```\n$ {command}\n```\n\n{output}"

            return ExecutionResult(
                success=success,
                message=message,
                data=result_data,
                function_name="shell_command",
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"❌ Failed to execute command: {str(e)}",
                data={
                    "command": command,
                    "error": str(e),
                    "clean_output": f"Error: {str(e)}",
                },
                function_name="shell_command",
            )

    def _parse_command_response(self, response: str) -> dict[str, Any] | None:
        """Parse LLM response for shell command generation"""
        try:
            import json
            import re

            # Clean response and extract JSON
            response = response.strip()

            # Remove control characters that can break JSON parsing
            response = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", response)

            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)

            return data

        except Exception:
            return None

    def _get_system_info(self) -> dict[str, str]:
        """Get system information for command generation"""
        system = platform.system().lower()

        # Detect shell
        shell = os.environ.get("SHELL", "/bin/bash")
        if "zsh" in shell:
            shell_type = "zsh"
        elif "bash" in shell:
            shell_type = "bash"
        elif "fish" in shell:
            shell_type = "fish"
        else:
            shell_type = "bash"  # default

        return {
            "os": system,
            "shell": shell_type,
            "platform": platform.platform(),
            "home_dir": os.path.expanduser("~"),
            "current_dir": os.getcwd(),
        }

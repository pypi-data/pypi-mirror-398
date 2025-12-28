# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Shell Command Functions - AI-powered shell command generation and execution"""


import asyncio
import os
import platform
import re
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


class ShellCommandFunction(FunctionPlugin):
    """Generate and execute shell commands based on natural language input"""

    @property
    def name(self) -> str:
        return "shell_command"

    @property
    def description(self) -> str:
        return (
            "Generate and execute shell commands based on natural language descriptions"
        )

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
                default=False,
                description="Whether to execute the command after generation (requires confirmation)",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # Always require confirmation for shell commands

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: standard mode to show command + result with metrics"""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check if LLM provider and shell access are available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for shell command generation"],
            )
        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Generate shell command and optionally execute with user confirmation"""

        request = parameters["request"]
        execute_command = parameters.get("execute", False)

        try:
            # Detect system information
            system_info = self._get_system_info()

            # Generate shell command using LLM
            if hasattr(context.llm_provider, "complete_with_usage"):
                llm_response = await context.llm_provider.complete_with_usage(
                    self._build_command_generation_prompt(request, system_info)
                )
                response_content = llm_response.content
                usage = llm_response.usage or {}
            else:
                # Fallback to regular completion
                response_content = await context.llm_provider.complete(
                    self._build_command_generation_prompt(request, system_info)
                )
                usage = {}

            # Parse the LLM response
            parsed_response = self._parse_command_response(response_content)

            if not parsed_response:
                return ExecutionResult(
                    success=False, message="Failed to generate a valid shell command"
                )

            command = parsed_response["command"]
            explanation = parsed_response.get("explanation", "Shell command generated")
            safety_notes = parsed_response.get("safety_notes", [])

            # Prepare result data
            result_data = {
                "command": command,
                "explanation": explanation,
                "system_info": system_info,
                "safety_notes": safety_notes,
                "thinking_mode": True,
                "provider": (
                    context.llm_provider.provider_name
                    if hasattr(context.llm_provider, "provider_name")
                    else "Unknown"
                ),
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "confidence": parsed_response.get("confidence", 85.0),
                "reasoning": f"Generated shell command for: {request}",
                "requires_execution_confirmation": execute_command,
                "timestamp": datetime.now().isoformat(),
            }

            # If execution is requested, prepare for confirmation
            if execute_command:
                result_data["requires_execution_confirmation"] = True
                result_data["pending_command"] = command

                # v0.6.0: Don't include confirmation prompt in message
                # Client will handle confirmation display and prompt
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data=result_data,
                )
            else:
                # Just return the generated command
                return ExecutionResult(
                    success=True,
                    message=f"Generated command: `{command}`\n\n{explanation}",
                    data=result_data,
                )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Shell command generation failed: {str(e)}"
            )

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

    def _build_command_generation_prompt(
        self, request: str, system_info: dict[str, str]
    ) -> str:
        """Build prompt for shell command generation"""

        return f"""You are an expert system administrator. Generate a shell command based on the user's natural language request.

System Information:
- OS: {system_info['os']}
- Shell: {system_info['shell']}
- Platform: {system_info['platform']}
- Home Directory: {system_info['home_dir']}
- Current Directory: {system_info['current_dir']}

User Request: "{request}"

Generate a safe, efficient shell command that accomplishes the user's request. Consider:
1. Use appropriate commands for the detected OS/shell
2. Include safety considerations (avoid destructive operations without explicit confirmation)
3. Use human-readable output when possible
4. Handle edge cases (empty results, permissions, etc.)
5. Prefer portable commands when possible

Respond with JSON in this format:
{{
  "command": "the actual shell command",
  "explanation": "clear explanation of what the command does",
  "safety_notes": ["list of safety considerations or warnings"],
  "confidence": 85.0,
  "reasoning": "why this command was chosen"
}}

Important: The command should be safe to run and accomplish exactly what the user requested. If the request is ambiguous, choose the most reasonable interpretation."""

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
            # Try parsing the JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as json_err:
                # Try to fix common JSON issues
                print(f"JSON parse error: {json_err}, attempting to fix...")

                # Fix unescaped newlines and quotes in explanation
                json_str = json_str.replace("\n", "\\n").replace("\r", "\\r")
                json_str = re.sub(r'(?<!\\)"(?=.*")', '\\"', json_str)

                try:
                    data = json.loads(json_str)
                    print("Successfully parsed after cleanup")
                except json.JSONDecodeError:
                    print("Could not fix JSON, falling back to regex extraction")
                    # Last resort: regex extraction
                    command_match = re.search(r'"command"\s*:\s*"([^"]+)"', response)
                    explanation_match = re.search(
                        r'"explanation"\s*:\s*"([^"]+)"', response
                    )

                    if command_match:
                        data = {
                            "command": command_match.group(1),
                            "explanation": (
                                explanation_match.group(1)
                                if explanation_match
                                else "Command generated"
                            ),
                        }
                    else:
                        return None

            # Validate required fields
            if "command" not in data:
                return None

            return data

        except (ValueError, KeyError) as e:
            print(f"Failed to parse command response: {e}")
            return None

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute a confirmed shell command"""
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
                output_lines.append("📤 Output:")
                output_lines.append(stdout.decode("utf-8", errors="ignore").strip())

            if stderr:
                output_lines.append("⚠️  Error output:")
                output_lines.append(stderr.decode("utf-8", errors="ignore").strip())

            if not stdout and not stderr:
                output_lines.append("✅ Command completed with no output")

            output_text = "\n".join(output_lines)

            # Prepare data with token information
            data = {
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore") if stdout else "",
                "stderr": stderr.decode("utf-8", errors="ignore") if stderr else "",
                "execution_time": datetime.now().isoformat(),
            }

            # Include original token usage if provided
            if original_tokens:
                data.update(
                    {
                        "input_tokens": original_tokens.get("input_tokens"),
                        "output_tokens": original_tokens.get("output_tokens"),
                    }
                )

            return ExecutionResult(
                success=process.returncode == 0,
                message=f"Command executed: `{command}`\n\n{output_text}",
                data=data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Command execution failed: {str(e)}",
                data={"command": command, "error": str(e)},
            )

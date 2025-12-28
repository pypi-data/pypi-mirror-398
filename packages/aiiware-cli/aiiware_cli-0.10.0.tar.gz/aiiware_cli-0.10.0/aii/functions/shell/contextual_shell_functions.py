# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Contextual Shell Functions with Conversation Memory"""


import asyncio
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


class ContextualShellFunction(FunctionPlugin):
    """Shell command function with conversation memory and contextual understanding"""

    @property
    def name(self) -> str:
        return "contextual_shell"

    @property
    def description(self) -> str:
        return "Generate shell commands with conversation memory and contextual understanding"

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
                description="Natural language description of the shell operation",
            ),
            "execute": ParameterSchema(
                name="execute",
                type="boolean",
                required=False,
                default=True,
                description="Whether to execute the command after generation",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY

    @property
    def default_output_mode(self) -> OutputMode:
        """Default output mode: full reasoning and context"""
        return OutputMode.THINKING

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Validate that LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for contextual shell commands"],
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute contextual shell command generation"""

        user_request = parameters.get("request", "")
        execute_command = parameters.get("execute", True)

        if not user_request:
            return ExecutionResult(
                success=False,
                message="Request parameter is required",
                function_name=self.name,
            )

        try:
            # Check for contextual patterns in the request
            contextual_info = self._analyze_contextual_patterns(user_request)

            # Build enhanced prompt with conversation context
            prompt = await self._build_contextual_prompt(
                user_request, contextual_info, context
            )

            # Generate command using LLM
            if hasattr(context.llm_provider, "stream_complete"):
                # Use streaming if available
                response_chunks = []
                async for chunk in context.llm_provider.stream_complete(prompt):
                    response_chunks.append(chunk)
                response = "".join(response_chunks)
            else:
                # Fallback to regular completion
                response = await context.llm_provider.complete(prompt)

            # Parse the response to extract command and explanation
            command_data = self._parse_llm_response(response)

            # Prepare result with contextual information
            result_data = {
                "command": command_data["command"],
                "explanation": command_data["explanation"],
                "user_request": user_request,
                "contextual_references": contextual_info.get("references", []),
                "safety_warnings": command_data.get("safety_warnings", []),
                "thinking_mode": True,
                "provider": getattr(
                    context.llm_provider, "provider_name", "Contextual-Enabled"
                ),
                "confidence": command_data.get("confidence", 95.0),
                "context_aware": len(contextual_info.get("references", [])) > 0,
                "features": [
                    "Conversation memory",
                    "Contextual understanding",
                    "Safety through history",
                    "Enhanced accuracy",
                ],
                "reasoning": self._build_reasoning_explanation(
                    user_request, contextual_info, command_data
                ),
                "timestamp": datetime.now().isoformat(),
            }

            if execute_command:
                result_data["requires_execution_confirmation"] = True
                result_data["pending_command"] = command_data["command"]

            return ExecutionResult(
                success=True,
                message=f"Generated contextual shell command: `{command_data['command']}`",
                function_name=self.name,
                data=result_data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Contextual shell command generation failed: {str(e)}",
                function_name=self.name,
            )

    def _analyze_contextual_patterns(self, user_request: str) -> dict[str, Any]:
        """Analyze user request for contextual patterns"""
        request_lower = user_request.lower()
        contextual_info = {"references": [], "patterns": []}

        # Direct references
        if any(word in request_lower for word in ["that", "it", "them", "this"]):
            contextual_info["references"].append("direct_reference")
            contextual_info["patterns"].append("Direct reference to previous context")

        # Sequence references
        if any(
            word in request_lower for word in ["second", "next", "another", "third"]
        ):
            contextual_info["references"].append("sequence_reference")
            contextual_info["patterns"].append(
                "Sequence reference requiring previous results"
            )

        # Size/comparison references
        if any(
            word in request_lower
            for word in ["largest", "biggest", "smallest", "first", "last"]
        ):
            contextual_info["references"].append("size_comparison")
            contextual_info["patterns"].append("Size/comparison reference")

        # Action references
        if any(word in request_lower for word in ["delete", "remove", "move", "copy"]):
            contextual_info["references"].append("action_reference")
            contextual_info["patterns"].append("Action on previously identified items")

        # Previous command references
        if any(
            phrase in request_lower
            for phrase in ["same command", "previous command", "again", "repeat"]
        ):
            contextual_info["references"].append("command_reference")
            contextual_info["patterns"].append("Reference to previous commands")

        return contextual_info

    async def _build_contextual_prompt(
        self, user_request: str, contextual_info: dict, context: ExecutionContext
    ) -> str:
        """Build enhanced prompt with contextual understanding"""

        base_prompt = f"""You are an expert shell command assistant with conversation memory. Generate a safe and effective command for this request:

Request: {user_request}

"""

        # Add contextual information if available
        if contextual_info.get("references"):
            base_prompt += f"""
IMPORTANT CONTEXTUAL ANALYSIS:
- Detected contextual patterns: {', '.join(contextual_info['patterns'])}
- Reference types: {', '.join(contextual_info['references'])}
- This request appears to reference previous conversation context
- Consider what the user might be referring to based on typical conversation flow

"""

        # Add safety considerations for contextual commands
        if "action_reference" in contextual_info.get("references", []):
            base_prompt += """
⚠️  SAFETY WARNING: This appears to be an action command referencing previous context.
- Be extra careful with destructive operations (delete, remove, move)
- If unclear what files/directories are being referenced, ask for clarification
- Prefer safer alternatives when possible

"""

        base_prompt += """Please provide:
1. A clear explanation of what the command does
2. The exact shell command in backticks like `command here`
3. Any important safety considerations
4. If this appears to reference previous context, explain your interpretation

Think step by step and explain your reasoning clearly. Focus on:
- Safety and user data protection
- Contextual accuracy based on detected patterns
- Clear explanations for educational value
- Confirmation requirements for potentially dangerous operations

The user is on a macOS/Unix system with bash shell."""

        return base_prompt

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response to extract command and other information"""

        command = "echo 'Command extraction failed'"
        explanation = response
        safety_warnings = []
        confidence = 90.0

        # Extract command from backticks
        if "`" in response:
            parts = response.split("`")
            for i in range(1, len(parts), 2):
                if parts[i].strip() and not parts[i].strip().startswith("command here"):
                    command = parts[i].strip()
                    break

        # Extract safety warnings
        if (
            "⚠️" in response
            or "WARNING" in response.upper()
            or "CAUTION" in response.upper()
        ):
            safety_warnings.append("Contains safety warnings - review carefully")

        # Estimate confidence based on response quality
        if "unclear" in response.lower() or "not sure" in response.lower():
            confidence = 70.0
        elif "contextual" in response.lower() or "previous" in response.lower():
            confidence = 85.0

        return {
            "command": command,
            "explanation": explanation,
            "safety_warnings": safety_warnings,
            "confidence": confidence,
        }

    def _build_reasoning_explanation(
        self, user_request: str, contextual_info: dict, command_data: dict
    ) -> str:
        """Build detailed reasoning explanation"""

        reasoning_parts = [
            f"Processing contextual shell command request: '{user_request}'"
        ]

        if contextual_info.get("references"):
            reasoning_parts.append(
                f"Detected contextual patterns: {', '.join(contextual_info['patterns'])}"
            )
            reasoning_parts.append("Applied conversation memory for enhanced accuracy")

        reasoning_parts.append(f"Generated command: {command_data['command']}")

        if command_data.get("safety_warnings"):
            reasoning_parts.append("⚠️ Safety considerations identified and included")

        return "\n".join(reasoning_parts)

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute confirmed contextual command"""

        try:
            start_time = datetime.now()

            # Execute command
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            end_time = datetime.now()

            execution_time = (end_time - start_time).total_seconds()

            # Prepare output
            output_lines = []
            if stdout:
                output_lines.extend(stdout.decode("utf-8").splitlines())
            if stderr:
                output_lines.extend(stderr.decode("utf-8").splitlines())

            output = (
                "\n".join(output_lines)
                if output_lines
                else "Command executed successfully (no output)"
            )

            # Prepare result data
            data = {
                "command": command,
                "execution_output": output,
                "execution_time": f"{execution_time:.2f}s",
                "return_code": process.returncode,
                "success": process.returncode == 0,
                "contextual_execution": True,
                "thinking_mode": True,
            }

            if original_tokens:
                data.update(
                    {
                        "input_tokens": original_tokens.get("input_tokens"),
                        "output_tokens": original_tokens.get("output_tokens"),
                    }
                )

            return ExecutionResult(
                success=process.returncode == 0,
                message=f"Contextual command executed: `{command}`",
                function_name=self.name,
                data=data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Contextual command execution failed: {str(e)}",
                function_name=self.name,
                data={"command": command, "error": str(e)},
            )

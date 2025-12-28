# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Streaming Shell Functions with Real-time AI Feedback"""


import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from ...cli.streaming_formatter import StreamingFormatter
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


class StreamingShellFunction(FunctionPlugin):
    """Shell command function with real-time streaming feedback"""

    @property
    def name(self) -> str:
        return "streaming_shell"

    @property
    def description(self) -> str:
        return "Generate shell commands with real-time AI reasoning and feedback"

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
            "stream": ParameterSchema(
                name="stream",
                type="boolean",
                required=False,
                default=True,
                description="Enable real-time streaming feedback",
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
        """Default output mode: result + metrics"""
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Validate that streaming LLM provider is available"""
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for streaming shell commands"],
            )

        # Check if provider supports streaming
        if not hasattr(context.llm_provider, "stream_complete"):
            return ValidationResult(
                valid=False, errors=["LLM provider does not support streaming"]
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute streaming shell command generation"""

        user_request = parameters.get("request", "")
        execute_command = parameters.get("execute", True)
        enable_streaming = parameters.get("stream", True)

        if not user_request:
            return ExecutionResult(
                success=False,
                message="Request parameter is required",
                function_name=self.name,
            )

        try:
            streaming_formatter = StreamingFormatter(use_colors=True, use_emojis=True)

            if enable_streaming and hasattr(context.llm_provider, "stream_complete"):
                # Generate command with streaming
                result = await self._generate_streaming_command(
                    user_request, context, streaming_formatter
                )
            else:
                # Fallback to regular generation
                result = await self._generate_regular_command(user_request, context)

            if not result.get("success", False):
                return ExecutionResult(
                    success=False,
                    message=f"Streaming command generation failed: {result.get('error', 'Unknown error')}",
                    function_name=self.name,
                )

            command = result.get("command", "")
            explanation = result.get("explanation", "")
            confidence = result.get("confidence", 95.0)

            # Display final result with streaming formatter
            streaming_formatter.display_streaming_result(
                command=command, explanation=explanation, confidence=confidence
            )

            # Prepare result data
            result_data = {
                "command": command,
                "explanation": explanation,
                "user_request": user_request,
                "thinking_mode": True,
                "provider": getattr(
                    context.llm_provider, "provider_name", "Streaming-Enabled"
                ),
                "confidence": confidence,
                "streaming_enabled": enable_streaming,
                "features": [
                    "Real-time streaming",
                    "Live AI reasoning",
                    "Interactive feedback",
                    "Enhanced UX",
                ],
                "reasoning": f"Streaming shell command for: {user_request}",
                "timestamp": datetime.now().isoformat(),
            }

            if execute_command:
                result_data["requires_execution_confirmation"] = True
                result_data["pending_command"] = command

            # v0.6.2: Include command in message for client display (WebSocket mode)
            # The streaming formatter displays on server console, but client needs the command too
            return ExecutionResult(
                success=True,
                message=f"Generated command: `{command}`\n\n{explanation}",
                function_name=self.name,
                data=result_data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Streaming shell command generation failed: {str(e)}",
                function_name=self.name,
            )

    async def _generate_streaming_command(
        self,
        user_request: str,
        context: ExecutionContext,
        formatter: StreamingFormatter,
    ) -> dict[str, Any]:
        """Generate command with real-time streaming"""

        try:
            # Build enhanced prompt for shell command generation
            prompt = self._build_streaming_prompt(user_request)

            # Create stream from LLM provider
            stream = context.llm_provider.stream_complete(prompt)

            # Stream the thinking process
            await formatter.stream_shell_thinking_mode(
                context="Shell command generation",
                request=user_request,
                provider=getattr(context.llm_provider, "provider_name", "Streaming"),
                stream_generator=stream,
            )

            # Generate command with streaming progress
            command_result = await formatter.stream_command_generation(
                request=user_request,
                provider=getattr(context.llm_provider, "provider_name", "Streaming"),
                command_stream=context.llm_provider.stream_complete(prompt),
            )

            return {
                "success": True,
                "command": command_result.get(
                    "command", "echo 'Command generation in progress'"
                ),
                "explanation": command_result.get(
                    "explanation", "Streaming command generated"
                ),
                "confidence": command_result.get("confidence", 95.0),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _generate_regular_command(
        self, user_request: str, context: ExecutionContext
    ) -> dict[str, Any]:
        """Fallback to regular command generation"""

        try:
            prompt = self._build_streaming_prompt(user_request)
            response = await context.llm_provider.complete(prompt)

            # Simple command extraction
            command = "echo 'Regular command generation'"
            if "`" in response and response.count("`") >= 2:
                parts = response.split("`")
                if len(parts) >= 2:
                    command = parts[1].strip()

            return {
                "success": True,
                "command": command,
                "explanation": response,
                "confidence": 90.0,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _build_streaming_prompt(self, user_request: str) -> str:
        """Build enhanced prompt for streaming command generation"""

        return f"""You are an expert shell command assistant. Generate a safe and effective command for this request:

Request: {user_request}

Please provide:
1. A clear explanation of what the command does
2. The exact shell command in backticks like `command here`
3. Any important safety considerations

Think step by step and explain your reasoning clearly. Focus on:
- Safety and user data protection
- Efficiency and best practices
- Clear explanations for educational value

The user is on a macOS/Unix system with bash shell."""

    async def execute_confirmed_command(
        self,
        command: str,
        context: ExecutionContext,
        original_tokens: dict[str, int] | None = None,
    ) -> ExecutionResult:
        """Execute confirmed command with streaming output"""

        try:
            streaming_formatter = StreamingFormatter()

            # Create async generator for command execution
            async def execution_stream() -> AsyncIterator[str]:
                """Stream command execution output"""
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                # Stream stdout in real-time
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    yield line.decode("utf-8", errors="ignore")

                # Wait for process completion
                await process.wait()

                # Get any remaining stderr
                stderr = await process.stderr.read()
                if stderr:
                    yield stderr.decode("utf-8", errors="ignore")

            # Stream the execution
            output = await streaming_formatter.stream_execution_feedback(
                command=command, execution_stream=execution_stream()
            )

            # Prepare execution data
            data = {
                "command": command,
                "execution_output": output,
                "execution_time": "< 1s",  # Would be calculated properly
                "streaming_enabled": True,
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
                success=True,
                message=f"Streaming command executed: `{command}`",
                data=data,
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Streaming command execution failed: {str(e)}",
                data={"command": command, "error": str(e)},
            )

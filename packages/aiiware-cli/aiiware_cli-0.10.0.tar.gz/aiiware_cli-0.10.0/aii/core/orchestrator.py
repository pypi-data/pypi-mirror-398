# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Universal LLM Orchestrator - Manages function calling and context gathering"""


import json
from datetime import datetime
from typing import Any

from ..core.registry.function_registry import FunctionRegistry

# Import context functions dynamically to avoid circular imports
from .models import ExecutionContext, ExecutionResult


class LLMOrchestrator:
    """Orchestrates LLM-driven function calling for universal intent handling"""

    def __init__(self, llm_provider: Any, function_registry: FunctionRegistry):
        self.llm_provider = llm_provider
        self.function_registry = function_registry
        self.context_functions = self._initialize_context_functions()

    def _initialize_context_functions(self) -> dict[str, Any]:
        """Initialize fundamental context gathering functions

        NOTE: Context gathering functions removed in v0.6.0.
        The orchestrator now works without automatic context gathering.
        Context should be provided by the client when needed (Client-Owned Workflow).

        See: system-dev-docs/aii-cli/issues/issue-005-v0.6.0-architecture-compliance-audit.md
        """
        # Return empty dict - no context functions available
        return {}

    async def process_universal_request(
        self, user_input: str, context: ExecutionContext
    ) -> ExecutionResult:
        """Process user request using universal function architecture"""

        # Step 1: Analyze user intent and determine needed context
        intent_analysis = await self._analyze_intent_and_context_needs(
            user_input, context
        )

        if not intent_analysis:
            return ExecutionResult(
                success=False, message="Could not analyze user intent"
            )

        # Step 2: Gather required context data
        context_data = await self._gather_context_data(intent_analysis, context)

        # Step 3: Generate final response with gathered context
        final_result = await self._generate_final_response(
            user_input, intent_analysis, context_data, context
        )

        return final_result

    async def _analyze_intent_and_context_needs(
        self, user_input: str, context: ExecutionContext
    ) -> dict[str, Any] | None:
        """Analyze user intent and determine what context functions to call"""

        available_functions = self._get_available_functions_description()

        prompt = f"""You are an intelligent function orchestrator. Analyze the user's request and determine:
1. What type of content/response they want
2. What context functions should be called to gather information
3. What parameters are needed for those functions

Available Context Functions:
{available_functions}

User Request: "{user_input}"

Respond with JSON only:
{{
  "intent_type": "content_generation|code_generation|git_operation|file_operation|system_query",
  "target_format": "tweet|email|post|code|commit_message|explanation|summary",
  "required_context": [
    {{
      "function": "git_context|file_context|system_context",
      "parameters": {{"key": "value"}}
    }}
  ],
  "reasoning": "Why these functions are needed"
}}"""

        try:
            response = await self.llm_provider.complete(prompt)
            return self._parse_intent_analysis(response)
        except Exception as e:
            print(f"Intent analysis failed: {e}")
            return None

    def _parse_intent_analysis(self, response: str) -> dict[str, Any] | None:
        """Parse LLM response for intent analysis"""
        try:
            # Clean response and extract JSON
            response = response.strip()
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                return None

            json_str = response[start_idx:end_idx]
            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse intent analysis: {e}")
            return None

    async def _gather_context_data(
        self, intent_analysis: dict[str, Any], context: ExecutionContext
    ) -> dict[str, Any]:
        """Gather context data by calling required functions"""

        context_data = {}
        required_context = intent_analysis.get("required_context", [])

        for context_req in required_context:
            function_name = context_req.get("function")
            parameters = context_req.get("parameters", {})

            if function_name in self.context_functions:
                try:
                    func = self.context_functions[function_name]
                    result = await func.execute(parameters, context)

                    if result.success:
                        context_data[function_name] = result.data
                    else:
                        context_data[function_name] = {"error": result.message}

                except Exception as e:
                    context_data[function_name] = {"error": str(e)}

        return context_data

    async def _generate_final_response(
        self,
        user_input: str,
        intent_analysis: dict[str, Any],
        context_data: dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Generate final response using gathered context"""

        target_format = intent_analysis.get("target_format")

        # Format context data for prompt
        context_summary = self._format_context_for_prompt(context_data)

        if target_format in ["tweet", "email", "post"]:
            return await self._generate_content(
                user_input, target_format, context_summary, context
            )
        elif target_format == "code":
            return await self._generate_code(user_input, context_summary, context)
        elif target_format == "commit_message":
            return await self._generate_commit_message(
                user_input, context_summary, context
            )
        else:
            return await self._generate_explanation(
                user_input, context_summary, context
            )

    def _format_context_for_prompt(self, context_data: dict[str, Any]) -> str:
        """Format gathered context data for LLM prompt"""

        context_lines = []

        # Git context
        if "git_context" in context_data and not context_data["git_context"].get(
            "error"
        ):
            git_data = context_data["git_context"].get("git_context", {})
            if "latest_commit" in git_data:
                commit = git_data["latest_commit"]
                context_lines.append("Latest Git Commit:")
                context_lines.append(f"  Subject: {commit.get('subject', 'N/A')}")
                context_lines.append(f"  Author: {commit.get('author', 'N/A')}")
                if commit.get("body"):
                    context_lines.append(f"  Body: {commit.get('body')}")

            if "status" in git_data:
                status = git_data["status"]
                if not status.get("clean", True):
                    context_lines.append(
                        f"Git Status: {len(status.get('staged', []))} staged, {len(status.get('modified', []))} modified"
                    )

        # File context
        if "file_context" in context_data and not context_data["file_context"].get(
            "error"
        ):
            file_data = context_data["file_context"].get("file_context", {})
            if "structure" in file_data:
                structure = file_data["structure"]
                context_lines.append(
                    f"Current Directory: {structure.get('name', 'N/A')}"
                )

        # System context
        if "system_context" in context_data and not context_data["system_context"].get(
            "error"
        ):
            sys_data = context_data["system_context"].get("system_context", {})
            if "working_dir" in sys_data:
                wd = sys_data["working_dir"]
                context_lines.append(
                    f"Working Directory: {wd.get('current_directory', 'N/A')}"
                )

        return "\n".join(context_lines) if context_lines else "No context available"

    async def _generate_content(
        self,
        user_input: str,
        target_format: str,
        context_summary: str,
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Generate content (tweets, posts, emails) with context"""

        format_instructions = {
            "tweet": "Create an engaging tweet (max 280 characters) with appropriate emojis and hashtags",
            "email": "Generate a professional email with proper subject line, greeting, body, and closing",
            "post": "Create a social media post with engaging tone and appropriate hashtags/emojis",
        }

        instruction = format_instructions.get(
            target_format, "Generate appropriate content"
        )

        prompt = f"""Generate {target_format} based on this request: {user_input}

Available Context:
{context_summary}

Instructions:
- {instruction}
- Use the provided context to make the content relevant and accurate
- For git-related content, reference the latest commit information
- Maintain professional yet engaging tone
- Return only the generated content, no additional explanation

Generate the {target_format}:"""

        try:
            # Check if streaming callback is provided
            streaming_callback = context.streaming_callback if hasattr(context, 'streaming_callback') else None

            # Use enhanced LLM provider with token tracking and streaming support
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await self.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback  # Enable streaming if callback provided
                )
                content = llm_response.content.strip()
                usage = llm_response.usage or {}
                # Debug: log usage data
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"[v0.5.1 DEBUG] LLM response type: {type(llm_response)}")
                logger.error(f"[v0.5.1 DEBUG] LLM usage data: {usage}")
                logger.error(f"[v0.5.1 DEBUG] LLM usage dict content: input={usage.get('input_tokens')}, output={usage.get('output_tokens')}")
            else:
                # Fallback to regular completion
                content = await self.llm_provider.complete(prompt)
                content = content.strip()
                usage = {}
                import logging
                logger = logging.getLogger(__name__)
                logger.warning("[v0.5.1 DEBUG] Using fallback completion (no token tracking)")

            # Extract token values with defaults
            input_tokens = usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("output_tokens", 0) or 0

            # Debug: Log final values
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"[v0.5.1 DEBUG] Final token values: input={input_tokens}, output={output_tokens}")

            return ExecutionResult(
                success=True,
                message=content,
                data={
                    "content": content,
                    "clean_output": content,  # Required for WebSocket streaming
                    "format": target_format,
                    "context_used": bool(context_summary.strip()),
                    "context_summary": context_summary,
                    "reasoning": f"Generated {target_format} using intelligent context orchestration",
                    "provider": (
                        self.llm_provider.model_info
                        if hasattr(self.llm_provider, "model_info")
                        else "Unknown"
                    ),
                    "input_tokens": input_tokens,  # Ensure integer, not None
                    "output_tokens": output_tokens,  # Ensure integer, not None
                    "confidence": 85.0,  # High confidence for orchestrated generation
                    "timestamp": datetime.now().isoformat(),
                    "thinking_mode": True,
                    "content_type": target_format,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Content generation failed: {str(e)}"
            )

    async def _generate_code(
        self, user_input: str, context_summary: str, context: ExecutionContext
    ) -> ExecutionResult:
        """Generate code with context awareness"""

        prompt = f"""Generate code based on this request: {user_input}

Available Context:
{context_summary}

Instructions:
- Write clean, production-ready code
- Include appropriate error handling
- Follow language-specific best practices
- Use context information to inform implementation details
- Return only the code, no additional explanation

Generate the code:"""

        try:
            # Check if streaming callback is provided
            streaming_callback = context.streaming_callback if hasattr(context, 'streaming_callback') else None

            # Use enhanced LLM provider with token tracking and streaming support (v0.5.1 fix)
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await self.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback  # Enable streaming if callback provided
                )
                code = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                # Fallback to regular completion
                code = await self.llm_provider.complete(prompt)
                code = code.strip()
                usage = {}

            # Clean markdown formatting if present
            if code.startswith("```"):
                lines = code.split("\n")
                if len(lines) > 2:
                    code = "\n".join(lines[1:-1])

            # Extract token values with defaults (v0.5.1 fix)
            input_tokens = usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("output_tokens", 0) or 0

            return ExecutionResult(
                success=True,
                message=f"Generated code:\n\n```\n{code}\n```",
                data={
                    "code": code,
                    "clean_output": code,  # Required for WebSocket streaming
                    "context_used": bool(context_summary.strip()),
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model": (
                        self.llm_provider.model_info
                        if hasattr(self.llm_provider, "model_info")
                        else None
                    ),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Code generation failed: {str(e)}"
            )

    async def _generate_commit_message(
        self, user_input: str, context_summary: str, context: ExecutionContext
    ) -> ExecutionResult:
        """Generate git commit message with context"""

        prompt = f"""Generate a conventional commit message based on: {user_input}

Available Context:
{context_summary}

Instructions:
- Follow conventional commit format: type(scope): description
- Use appropriate commit types (feat, fix, docs, style, refactor, test, chore)
- Keep subject line under 50 characters
- Include body if needed with more details
- Use context information to determine appropriate message

Generate the commit message:"""

        try:
            # Check if streaming callback is provided
            streaming_callback = context.streaming_callback if hasattr(context, 'streaming_callback') else None

            # Use enhanced LLM provider with token tracking and streaming support (v0.5.1 fix)
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await self.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback  # Enable streaming if callback provided
                )
                commit_msg = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                # Fallback to regular completion
                commit_msg = await self.llm_provider.complete(prompt)
                commit_msg = commit_msg.strip()
                usage = {}

            # Extract token values with defaults (v0.5.1 fix)
            input_tokens = usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("output_tokens", 0) or 0

            return ExecutionResult(
                success=True,
                message=f"Generated commit message:\n\n{commit_msg}",
                data={
                    "commit_message": commit_msg,
                    "clean_output": commit_msg,  # Required for WebSocket streaming
                    "context_used": bool(context_summary.strip()),
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model": (
                        self.llm_provider.model_info
                        if hasattr(self.llm_provider, "model_info")
                        else None
                    ),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Commit message generation failed: {str(e)}"
            )

    async def _generate_explanation(
        self, user_input: str, context_summary: str, context: ExecutionContext
    ) -> ExecutionResult:
        """Generate explanations and summaries with context"""

        prompt = f"""Provide a comprehensive response to: {user_input}

Available Context:
{context_summary}

Instructions:
- Provide clear, accurate information
- Use context to make the response relevant to the current situation
- Structure the response logically
- Include examples where helpful
- Be concise but thorough

Generate the response:"""

        try:
            # Check if streaming callback is provided
            streaming_callback = context.streaming_callback if hasattr(context, 'streaming_callback') else None

            # Use enhanced LLM provider with token tracking and streaming support (v0.5.1 fix)
            if hasattr(self.llm_provider, "complete_with_usage"):
                llm_response = await self.llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback  # Enable streaming if callback provided
                )
                response = llm_response.content.strip()
                usage = llm_response.usage or {}
            else:
                # Fallback to regular completion
                response = await self.llm_provider.complete(prompt)
                response = response.strip()
                usage = {}

            # Extract token values with defaults (v0.5.1 fix)
            input_tokens = usage.get("input_tokens", 0) or 0
            output_tokens = usage.get("output_tokens", 0) or 0

            return ExecutionResult(
                success=True,
                message=response,
                data={
                    "response": response,
                    "clean_output": response,  # Required for WebSocket streaming
                    "context_used": bool(context_summary.strip()),
                    "timestamp": datetime.now().isoformat(),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model": (
                        self.llm_provider.model_info
                        if hasattr(self.llm_provider, "model_info")
                        else None
                    ),
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False, message=f"Response generation failed: {str(e)}"
            )

    def _get_available_functions_description(self) -> str:
        """Get descriptions of available context functions"""

        descriptions = []

        for func_name, func in self.context_functions.items():
            descriptions.append(f"- {func_name}: {func.description}")

        return "\n".join(descriptions)

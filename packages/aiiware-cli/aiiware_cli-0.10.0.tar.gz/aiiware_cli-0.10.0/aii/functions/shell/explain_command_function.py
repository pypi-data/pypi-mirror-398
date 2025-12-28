# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Explain complex shell commands with safety analysis.

Features:
- LLM-powered command breakdown
- Safety risk analysis (safe/caution/dangerous)
- Suggest safer alternatives
- Example output visualization
"""


import json
from typing import Dict, Any
from aii.core.models import FunctionPlugin, FunctionSafety, ExecutionResult, ExecutionContext, OutputMode, FunctionCategory


class ExplainCommandFunction(FunctionPlugin):
    """
    Explain what a SHELL COMMAND does, with safety analysis.

    Use this for shell/bash commands with syntax (flags, pipes, etc).
    For concepts, use the 'explain' function instead.

    Examples:
    - aii explain-cmd "find . -name '*.py' | xargs rm"
    - aii explain "git reset --hard HEAD~3"
    - aii "what does rm -rf do?"
    """

    # Legacy attributes (for compatibility)
    function_name = "explain_command"
    function_description = """Explain what a shell/bash COMMAND does with detailed safety analysis.

Use this function when the user wants to understand a SPECIFIC shell command.

Common patterns:
- "explain this command: [command]"
- "what does [command] do"
- "explain: [command]"
- "describe this command: [command]"
- "analyze [command]"

The 'command' parameter should contain the actual shell command to explain.
Extract the command from user input - everything after keywords like "explain this command:", "what does", etc.

IMPORTANT: Use this ONLY when the user provides an actual command with shell syntax (flags, pipes, redirection).
For general concepts, use the 'explain' function instead.

Shell command indicators:
- Contains flags: --, -, -la, -rf, --help
- Contains pipes: |
- Contains redirection: >, >>, <
- Shell commands: find, grep, rm, chmod, ls, git, curl, etc.

Examples:
- "explain this command: find . -name '*.py'" → command: "find . -name '*.py'"
- "what does rm -rf / do" → command: "rm -rf /"
- "explain: ls -la | grep foo" → command: "ls -la | grep foo"
- "what does docker ps -a do" → command: "docker ps -a"

Output: Detailed breakdown of the command with safety analysis."""

    @property
    def name(self) -> str:
        return "explain_command"

    @property
    def description(self) -> str:
        return self.function_description

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, Any]:
        from aii.core.models import ParameterSchema
        return {
            "command": ParameterSchema(
                name="command",
                type="string",
                required=True,
                description="The actual shell command to explain. Extract from user input after keywords like 'explain this command:', 'what does', 'explain:', etc.",
            ),
            "detail_level": ParameterSchema(
                name="detail_level",
                type="string",
                required=False,
                default="detailed",
                choices=["basic", "detailed", "expert"],
                description="Level of detail in explanation",
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return False

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.CLEAN  # Users want just the explanation

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(self, context: ExecutionContext):
        """Check if LLM provider is available"""
        from aii.core.models import ValidationResult
        if not context.llm_provider:
            return ValidationResult(
                valid=False,
                errors=["LLM provider required for command explanation"]
            )
        return ValidationResult(valid=True)

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute command explanation with LLM analysis."""

        command = parameters.get("command", "")
        detail_level = parameters.get("detail_level", "detailed")

        if not command:
            return ExecutionResult(
                success=False,
                message="No command provided to explain",
                data={"clean_output": "Error: No command provided"}
            )

        # Check if LLM is available
        if not context.llm_provider:
            return ExecutionResult(
                success=False,
                message="LLM provider required for command explanation",
                data={"clean_output": "Error: LLM provider required. Run: aii config init"}
            )

        try:
            # LLM-powered command analysis
            explanation, usage = await self._analyze_command(
                command,
                detail_level,
                context.llm_provider
            )

            # Format output
            output = self._format_explanation(explanation)

            return ExecutionResult(
                success=True,
                message=output,
                data={
                    "command": command,
                    "explanation": explanation,
                    "clean_output": output,  # For CLEAN mode
                    # Token tracking (v0.6.0)
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                }
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Failed to explain command: {str(e)}",
                data={"clean_output": f"Error: {str(e)}"}
            )

    async def _analyze_command(
        self,
        command: str,
        detail_level: str,
        llm_provider
    ) -> tuple[Dict[str, Any], Dict[str, int]]:
        """Use LLM to analyze command comprehensively."""

        prompt = f"""You are a shell command expert. Analyze this command comprehensively:

Command: {command}

Provide a detailed analysis with the following structure:

1. **Summary**: One-line description of what the command does

2. **Breakdown**: Explain each part of the command (split by pipes, flags, arguments)
   Format as a list of objects with:
   - syntax: the exact part of the command
   - description: what it does

3. **Safety Analysis**:
   - level: "safe" | "caution" | "dangerous"
   - risks: list of potential risks (can be empty for safe commands)
   - recommendations: list of safety recommendations (can be empty for safe commands)

4. **Alternatives**: Safer or more efficient alternative commands (can be empty if command is already safe/optimal)

5. **Example Output**: Show what the command would typically produce (brief example)

Detail level: {detail_level}

Return ONLY valid JSON with this exact structure (no markdown, no code blocks):
{{
  "summary": "...",
  "breakdown": [
    {{"syntax": "...", "description": "..."}},
    ...
  ],
  "safety": {{
    "level": "safe",
    "risks": ["...", ...],
    "recommendations": ["...", ...]
  }},
  "alternatives": ["...", ...],
  "example_output": "..."
}}
"""

        try:
            # Use LLM to generate structured response
            # Prefer complete_with_usage for token tracking (v0.6.0)
            usage = {}
            if hasattr(llm_provider, 'complete_with_usage') and callable(llm_provider.complete_with_usage):
                llm_response = await llm_provider.complete_with_usage(prompt)
                response = llm_response.content
                usage = llm_response.usage or {}
            elif hasattr(llm_provider, 'complete') and callable(llm_provider.complete):
                response = await llm_provider.complete(prompt)
            elif hasattr(llm_provider, 'generate') and callable(llm_provider.generate):
                response = await llm_provider.generate(prompt)
            else:
                raise AttributeError("LLM provider has no compatible method (complete/complete_with_usage/generate)")

            # Parse JSON response
            # Clean response (remove markdown code blocks if present)
            response_text = response.strip()
            if response_text.startswith("```"):
                # Remove code block markers
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()

            explanation = json.loads(response_text)

            # Validate structure
            required_keys = ["summary", "breakdown", "safety", "alternatives", "example_output"]
            for key in required_keys:
                if key not in explanation:
                    explanation[key] = {} if key == "safety" else [] if key in ["breakdown", "alternatives"] else ""

            # Ensure safety has required fields
            if "level" not in explanation["safety"]:
                explanation["safety"]["level"] = "unknown"
            if "risks" not in explanation["safety"]:
                explanation["safety"]["risks"] = []
            if "recommendations" not in explanation["safety"]:
                explanation["safety"]["recommendations"] = []

            return explanation, usage

        except json.JSONDecodeError as e:
            # Fallback with basic structure
            return {
                "summary": f"Command: {command}",
                "breakdown": [{"syntax": command, "description": "Unable to parse detailed breakdown"}],
                "safety": {
                    "level": "unknown",
                    "risks": ["Could not analyze safety - please verify command before running"],
                    "recommendations": ["Consult command documentation"]
                },
                "alternatives": [],
                "example_output": "Unable to generate example"
            }, {}
        except Exception as e:
            # Fallback on any error
            return {
                "summary": f"Command: {command}",
                "breakdown": [{"syntax": command, "description": f"Analysis error: {str(e)}"}],
                "safety": {
                    "level": "unknown",
                    "risks": ["Unable to analyze command safety"],
                    "recommendations": []
                },
                "alternatives": [],
                "example_output": ""
            }, {}

    def _format_explanation(self, explanation: Dict[str, Any]) -> str:
        """Format explanation for CLI output."""

        output = []

        # Summary
        output.append("📝 Command Summary")
        output.append(f"{explanation.get('summary', 'N/A')}\n")

        # Breakdown
        breakdown = explanation.get('breakdown', [])
        if breakdown:
            output.append("🔍 Breakdown:")
            for i, part in enumerate(breakdown, 1):
                syntax = part.get('syntax', '')
                desc = part.get('description', '')
                output.append(f"  {i}. `{syntax}`")
                output.append(f"     → {desc}")
            output.append("")

        # Safety analysis
        safety = explanation.get('safety', {})
        safety_level = safety.get('level', 'unknown')
        safety_icons = {
            "safe": "✅",
            "caution": "⚠️",
            "dangerous": "🚨",
            "unknown": "❓"
        }

        icon = safety_icons.get(safety_level, "❓")
        output.append(f"{icon} Safety: {safety_level.upper()}")

        risks = safety.get('risks', [])
        if risks:
            output.append("Potential Risks:")
            for risk in risks:
                output.append(f"  • {risk}")

        recommendations = safety.get('recommendations', [])
        if recommendations:
            output.append("\nRecommendations:")
            for rec in recommendations:
                output.append(f"  • {rec}")

        output.append("")

        # Alternatives
        alternatives = explanation.get('alternatives', [])
        if alternatives:
            output.append("💡 Safer/Better Alternatives:")
            for alt in alternatives:
                output.append(f"  • `{alt}`")
            output.append("")

        # Example output
        example = explanation.get('example_output', '')
        if example:
            output.append("📄 Example Output:")
            output.append("```")
            output.append(example)
            output.append("```")

        return "\n".join(output)

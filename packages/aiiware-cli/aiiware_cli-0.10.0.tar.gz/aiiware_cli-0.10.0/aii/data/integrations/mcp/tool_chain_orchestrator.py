# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Tool Chain Orchestrator for Multi-Step MCP Tool Execution (v0.4.8)

This module enables automatic execution of sequential MCP tool calls where
the output of one tool becomes the input to another.
"""


import json
import re
from dataclasses import dataclass
from typing import Any, Optional
from datetime import datetime

from ....data.providers.llm_provider import LLMProvider
from .client_manager import MCPClientManager
from .models import ToolCallResult


@dataclass
class ChainStep:
    """Represents a single step in a tool chain"""
    step: int
    tool_name: str
    parameters: dict[str, Any]
    output_mapping: Optional[dict[str, str]] = None
    result: Optional[ToolCallResult] = None
    execution_time: float = 0.0


@dataclass
class ChainPlan:
    """Represents a complete tool chain execution plan"""
    requires_chaining: bool
    steps: list[ChainStep]
    reasoning: str
    total_estimated_cost: float = 0.0


@dataclass
class ChainResult:
    """Result of executing a tool chain"""
    success: bool
    steps: list[ChainStep]
    final_result: Optional[ToolCallResult]
    error: Optional[str] = None
    total_time: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class ToolChainOrchestrator:
    """Orchestrates multi-step MCP tool execution chains"""

    def __init__(
        self,
        mcp_client: MCPClientManager,
        llm_provider: Optional[LLMProvider] = None,
        max_chain_length: int = 5,
        verbose: bool = False
    ):
        self.mcp_client = mcp_client
        self.llm_provider = llm_provider
        self.max_chain_length = max_chain_length
        self.verbose = verbose
        # Token usage tracking for orchestrator LLM calls
        self._orchestrator_input_tokens = 0
        self._orchestrator_output_tokens = 0

    async def should_chain(self, user_input: str, tool_name: str, parameters: dict[str, Any]) -> bool:
        """Determine if multi-step chaining is needed for this request

        Args:
            user_input: Original user request
            tool_name: Initially selected tool name
            parameters: Initially selected parameters

        Returns:
            True if chaining is needed, False otherwise
        """
        if not self.llm_provider:
            return False

        # Quick heuristics to avoid unnecessary LLM calls
        # If user explicitly mentions a single tool, don't chain
        if "invoke" in user_input.lower() and tool_name in user_input:
            return False

        # If parameters look complete and specific, probably don't need chaining
        # (This is a heuristic - LLM will make final decision)

        try:
            # Get available tools for context
            all_tools = await self.mcp_client.discover_all_tools()
            tool_schemas = {
                tool.name: {
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
                for tool in all_tools
            }

            prompt = f"""Analyze if this request requires multiple MCP tool calls in sequence.

User Request: {user_input}
Initially Selected Tool: {tool_name}
Initially Selected Parameters: {json.dumps(parameters, ensure_ascii=False)}

Available MCP Tools: {json.dumps(tool_schemas, ensure_ascii=False, indent=2)}

Determine if multiple tools are needed (e.g., converting data before querying, or fetching IDs before operations).

Return ONLY valid JSON:
{{
  "requires_chaining": true or false,
  "reasoning": "brief explanation"
}}"""

            llm_response = await self.llm_provider.complete_with_usage(prompt)
            response = llm_response.content

            # Track token usage
            usage = llm_response.usage
            self._orchestrator_input_tokens += usage.get("input_tokens", 0)
            self._orchestrator_output_tokens += usage.get("output_tokens", 0)

            # Parse response - extract JSON from markdown code fences if present
            try:
                response_text = response.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                result = json.loads(response_text)
                return result.get("requires_chaining", False)
            except json.JSONDecodeError:
                if self.verbose:
                    print(f"⚠️ Failed to parse chaining decision: {response}")
                return False

        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error checking if chaining needed: {e}")
            return False

    async def plan_chain(self, user_input: str, tool_name: str, parameters: dict[str, Any]) -> Optional[ChainPlan]:
        """Plan the tool chain execution sequence using LLM

        Args:
            user_input: Original user request
            tool_name: Initially selected tool name
            parameters: Initially selected parameters

        Returns:
            ChainPlan if successful, None otherwise
        """
        if not self.llm_provider:
            return None

        try:
            # Get available tools
            all_tools = await self.mcp_client.discover_all_tools()
            tool_schemas = {
                tool.name: {
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
                for tool in all_tools
            }

            prompt = f"""You are an MCP tool orchestration assistant. Create a detailed execution plan for this request.

User Request: {user_input}
Initially Selected Tool: {tool_name}
Initially Selected Parameters: {json.dumps(parameters, ensure_ascii=False)}

Available MCP Tools: {json.dumps(tool_schemas, ensure_ascii=False, indent=2)}

Create a step-by-step execution plan. For parameter values that depend on previous steps, use this syntax:
- ${{step<N>.<json_path>}} to reference output from previous step
- Example: ${{step1.北京.station_code}} extracts the station_code for 北京 from step 1

IMPORTANT RULES:
- Do NOT use placeholder values like "YOUR_GITHUB_USERNAME", "USERNAME", "YOUR_TOKEN", etc.
- For GitHub authenticated queries (GitHub MCP server has GITHUB_PERSONAL_ACCESS_TOKEN):
  * For "my repositories": use search_repositories with query "user:@me" (NOT "user:USERNAME")
  * For "my issues": use search_issues with query "author:@me"
  * Use @me as the authenticated user identifier, NOT placeholders
  * Do NOT try to fetch username first - @me works directly
- Only create multi-step chains when truly necessary (e.g., need to fetch IDs before operations)
- If a single tool call can accomplish the task, set "requires_chaining": false

Return ONLY valid JSON:
{{
  "requires_chaining": true,
  "steps": [
    {{
      "step": 1,
      "tool_name": "first-tool-name",
      "parameters": {{"param": "value"}},
      "output_mapping": {{
        "output_field_path": "next_param_name"
      }}
    }},
    {{
      "step": 2,
      "tool_name": "second-tool-name",
      "parameters": {{
        "param": "${{step1.output.field}}"
      }}
    }}
  ],
  "reasoning": "explanation of the chain"
}}"""

            llm_response = await self.llm_provider.complete_with_usage(prompt)
            response = llm_response.content

            # Track token usage
            usage = llm_response.usage
            self._orchestrator_input_tokens += usage.get("input_tokens", 0)
            self._orchestrator_output_tokens += usage.get("output_tokens", 0)

            # Parse response - extract JSON from markdown code fences if present
            try:
                response_text = response.strip()
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                plan_data = json.loads(response_text)

                if not plan_data.get("requires_chaining", False):
                    return None

                steps = []
                for step_data in plan_data.get("steps", []):
                    step = ChainStep(
                        step=step_data["step"],
                        tool_name=step_data["tool_name"],
                        parameters=step_data.get("parameters", {}),
                        output_mapping=step_data.get("output_mapping")
                    )
                    steps.append(step)

                # Enforce max chain length
                if len(steps) > self.max_chain_length:
                    if self.verbose:
                        print(f"⚠️ Chain too long ({len(steps)} > {self.max_chain_length}), truncating")
                    steps = steps[:self.max_chain_length]

                return ChainPlan(
                    requires_chaining=True,
                    steps=steps,
                    reasoning=plan_data.get("reasoning", "Multi-step execution required")
                )

            except json.JSONDecodeError as e:
                if self.verbose:
                    print(f"⚠️ Failed to parse chain plan: {response}")
                    print(f"   Error: {e}")
                return None

        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error planning chain: {e}")
            return None

    def _resolve_parameters(self, parameters: dict[str, Any], previous_results: list[ChainStep]) -> dict[str, Any]:
        """Resolve parameter values that reference previous step outputs

        Args:
            parameters: Parameters that may contain ${stepN.path} references
            previous_results: List of completed steps with results

        Returns:
            Parameters with resolved values
        """
        resolved = {}

        for key, value in parameters.items():
            if isinstance(value, str) and "${step" in value:
                # Extract step references: ${step1.field.subfield}
                resolved_value = value

                # Find all ${...} patterns
                pattern = r'\$\{step(\d+)\.([^}]+)\}'
                matches = re.finditer(pattern, value)

                for match in matches:
                    step_num = int(match.group(1))
                    json_path = match.group(2)

                    # Find the step result
                    step_result = next((s for s in previous_results if s.step == step_num), None)
                    if not step_result or not step_result.result:
                        if self.verbose:
                            print(f"⚠️ Could not resolve ${{{match.group(0)}}}: step {step_num} not found or failed")
                        continue

                    # Extract value using JSON path
                    extracted_value = self._extract_json_path(step_result.result, json_path)
                    if extracted_value is not None:
                        resolved_value = resolved_value.replace(match.group(0), str(extracted_value))
                    else:
                        if self.verbose:
                            print(f"⚠️ Could not extract {json_path} from step {step_num} result")

                resolved[key] = resolved_value
            else:
                resolved[key] = value

        return resolved

    def _extract_json_path(self, result: ToolCallResult, json_path: str) -> Optional[Any]:
        """Extract value from MCP tool result using JSON path notation

        Args:
            result: MCP tool result
            json_path: Dot-notation path (e.g., "data.field.subfield" or "results[0].id")
                      Special handling for date operations: "tomorrow" calculates next day

        Returns:
            Extracted value or None if path not found
        """
        try:
            # Parse result content into dict
            result_data = {}
            result_text = None
            for item in result.content:
                if hasattr(item, 'text'):
                    result_text = item.text
                    # Try to parse text as JSON
                    try:
                        result_data = json.loads(item.text)
                        break
                    except json.JSONDecodeError:
                        result_data = {"text": item.text}
                elif hasattr(item, 'data'):
                    result_data = item.data
                    break

            # Special handling for date calculations
            # If the path contains "tomorrow" and we have a plain text date response
            if "tomorrow" in json_path.lower() and result_text and result_text.strip():
                # Try to parse as ISO date (YYYY-MM-DD)
                try:
                    from datetime import datetime, timedelta
                    # Clean the text (remove quotes, whitespace)
                    date_text = result_text.strip().strip('"').strip("'")
                    current_date = datetime.strptime(date_text, "%Y-%m-%d")
                    tomorrow = current_date + timedelta(days=1)
                    return tomorrow.strftime("%Y-%m-%d")
                except ValueError:
                    if self.verbose:
                        print(f"⚠️ Could not parse date from: {result_text}")

            # Navigate the JSON path
            current = result_data
            parts = json_path.split('.')

            for part in parts:
                # Handle array indexing: field[0]
                if '[' in part:
                    field, index = part.split('[')
                    index = int(index.rstrip(']'))
                    current = current[field][index]
                else:
                    current = current[part]

            return current

        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            if self.verbose:
                print(f"⚠️ Error extracting {json_path}: {e}")
            return None

    async def execute_chain(self, plan: ChainPlan) -> ChainResult:
        """Execute a tool chain according to the plan

        Args:
            plan: Chain execution plan

        Returns:
            ChainResult with execution details
        """
        start_time = datetime.now()
        completed_steps = []
        total_input_tokens = 0
        total_output_tokens = 0

        try:
            for step in plan.steps:
                step_start = datetime.now()

                if self.verbose:
                    print(f"\n🔗 Step {step.step}/{len(plan.steps)}: {step.tool_name}")

                # Resolve parameters that reference previous steps
                resolved_params = self._resolve_parameters(step.parameters, completed_steps)

                if self.verbose:
                    print(f"   Input: {json.dumps(resolved_params, ensure_ascii=False)}")

                # Execute the tool
                result = await self.mcp_client.call_tool(step.tool_name, resolved_params)

                step.result = result
                step.execution_time = (datetime.now() - step_start).total_seconds()

                if result.success:
                    if self.verbose:
                        print(f"   ✓ Complete ({step.execution_time:.1f}s)")
                    completed_steps.append(step)
                else:
                    # Step failed - abort chain
                    error_msg = result.error or "Unknown error"
                    if self.verbose:
                        print(f"   ✗ Failed: {error_msg}")

                    total_time = (datetime.now() - start_time).total_seconds()
                    return ChainResult(
                        success=False,
                        steps=completed_steps + [step],
                        final_result=None,
                        error=f"Step {step.step} failed: {error_msg}",
                        total_time=total_time,
                        total_input_tokens=total_input_tokens + self._orchestrator_input_tokens,
                        total_output_tokens=total_output_tokens + self._orchestrator_output_tokens
                    )

            # All steps completed successfully
            total_time = (datetime.now() - start_time).total_seconds()
            final_result = completed_steps[-1].result if completed_steps else None

            return ChainResult(
                success=True,
                steps=completed_steps,
                final_result=final_result,
                total_time=total_time,
                total_input_tokens=total_input_tokens + self._orchestrator_input_tokens,
                total_output_tokens=total_output_tokens + self._orchestrator_output_tokens
            )

        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            return ChainResult(
                success=False,
                steps=completed_steps,
                final_result=None,
                error=f"Chain execution error: {str(e)}",
                total_time=total_time,
                total_input_tokens=total_input_tokens + self._orchestrator_input_tokens,
                total_output_tokens=total_output_tokens + self._orchestrator_output_tokens
            )

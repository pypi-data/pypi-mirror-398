# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Advanced Shell Command Agent using Pydantic AI with native tool calling"""


import os

from pydantic_ai import Agent
from pydantic_ai.models import infer_model

from ..tools.shell_tools import (
    create_file_search_tool,
    create_shell_command_tool,
    execute_shell_command,
)


class ShellCommandAgent:
    """Advanced shell command agent with native Pydantic AI tool calling"""

    def __init__(self, provider_name: str, api_key: str, model: str):
        self.provider_name = provider_name.lower()
        self.api_key = api_key
        self.model = model
        self._setup_environment()
        self._create_agent()

    def _setup_environment(self):
        """Set up environment variables for Pydantic AI"""
        if self.provider_name == "openai":
            os.environ["OPENAI_API_KEY"] = self.api_key
        elif self.provider_name == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = self.api_key
        elif self.provider_name == "gemini":
            os.environ["GEMINI_API_KEY"] = self.api_key

    def _create_agent(self):
        """Create the Pydantic AI agent with shell command tools"""

        # Map to Pydantic AI model names
        model_mapping = {
            "openai": {
                "gpt-4": "openai:gpt-4",
                "gpt-4-turbo": "openai:gpt-4-turbo-preview",
                "default": "openai:gpt-4",
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": "anthropic:claude-3-5-sonnet-20241022",
                "default": "anthropic:claude-3-5-sonnet-20241022",
            },
            "gemini": {
                "gemini-2.0-flash": "gemini-2.0-flash-exp",
                "gemini-1.5-flash": "gemini-1.5-flash",
                "default": "gemini-2.0-flash-exp",
            },
        }

        provider_models = model_mapping.get(self.provider_name, {})
        pydantic_model = provider_models.get(
            self.model, provider_models.get("default", self.model)
        )

        # Create agent with tools
        self.agent = Agent(
            model=infer_model(pydantic_model),
            system_prompt="""You are an expert shell command assistant that helps users generate safe and effective command-line operations.

Your responsibilities:
1. Understand user requests for file operations, system information, and command-line tasks
2. Generate appropriate shell commands using the available tools
3. Provide clear explanations of what each command does
4. Include safety warnings when necessary
5. Always prioritize user safety and data protection

When a user asks for shell commands:
1. Use the generate_shell_command tool for general command generation
2. Use the search_files tool for file search operations
3. Provide detailed explanations and safety notes
4. Set appropriate confidence levels based on command complexity

Available tools can help with:
- Finding largest files in directories
- Listing directory contents
- Checking disk usage
- File search operations
- System information queries

Always explain commands clearly and include safety considerations.""",
            tools=[create_shell_command_tool(), create_file_search_tool()],
        )

    async def generate_command(self, user_request: str) -> dict[str, any]:
        """Generate a shell command based on user request using native tool calling"""

        try:
            # Run the agent - it will automatically decide which tool to use
            result = await self.agent.run(user_request)

            # Extract the tool call result if it's a ShellCommandResponse
            if hasattr(result, "output") and isinstance(result.output, str):
                # Parse the response to extract command information
                # The agent should have used tools to generate structured data
                return {
                    "success": True,
                    "command": "Generated via tool calling",
                    "explanation": result.output,
                    "confidence": 95.0,
                    "provider": f"PydanticAI:{self.model}",
                    "usage": self._extract_usage(result),
                }
            else:
                # Direct tool result
                return {
                    "success": True,
                    "command": getattr(result.output, "command", "Unknown"),
                    "explanation": getattr(result.output, "explanation", result.output),
                    "confidence": getattr(result.output, "confidence", 95.0),
                    "provider": f"PydanticAI:{self.model}",
                    "usage": self._extract_usage(result),
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": "",
                "explanation": f"Failed to generate command: {str(e)}",
                "confidence": 0.0,
                "provider": f"PydanticAI:{self.model}",
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            }

    async def execute_command(self, command: str) -> dict[str, any]:
        """Execute a shell command with timing and safety checks"""

        # Safety check - avoid dangerous commands
        dangerous_patterns = ["rm -rf", "sudo", "chmod 777", "dd if=", "mkfs", "format"]
        if any(pattern in command.lower() for pattern in dangerous_patterns):
            return {
                "success": False,
                "error": "Command blocked for safety reasons",
                "execution_output": "⚠️ Potentially dangerous command blocked",
                "execution_time": "0.00s",
            }

        try:
            result = await execute_shell_command(command)
            return {
                "success": result["success"],
                "execution_output": result["raw_output"],
                "execution_time": result["execution_time"],
                "return_code": result["return_code"],
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_output": f"Execution failed: {str(e)}",
                "execution_time": "0.00s",
            }

    def _extract_usage(self, result) -> dict[str, int]:
        """Extract usage information from Pydantic AI result"""
        usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        if hasattr(result, "usage") and result.usage:
            if hasattr(result.usage, "request_tokens"):
                usage["input_tokens"] = result.usage.request_tokens or 0
            elif hasattr(result.usage, "input_tokens"):
                usage["input_tokens"] = result.usage.input_tokens or 0

            if hasattr(result.usage, "response_tokens"):
                usage["output_tokens"] = result.usage.response_tokens or 0
            elif hasattr(result.usage, "output_tokens"):
                usage["output_tokens"] = result.usage.output_tokens or 0

            usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]

        return usage

    @property
    def provider_info(self) -> str:
        """Get formatted provider information"""
        return f"PydanticAI:{self.model}"

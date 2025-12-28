# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Pydantic AI Tools for Shell Command Generation and Execution"""


import asyncio
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_ai import Tool


class ShellCommandRequest(BaseModel):
    """Structured request for shell command generation"""

    user_request: str = Field(description="The user's natural language request")
    operating_system: str = Field(
        default="macos", description="Target operating system"
    )
    shell: str = Field(default="bash", description="Target shell environment")


class ShellCommandResponse(BaseModel):
    """Structured response with generated shell command"""

    command: str = Field(description="The generated shell command")
    explanation: str = Field(
        description="Detailed explanation of what the command does"
    )
    safety_notes: list[str] = Field(
        default_factory=list, description="Important safety warnings"
    )
    confidence: float = Field(description="Confidence score (0.0 to 100.0)")
    requires_confirmation: bool = Field(
        default=True, description="Whether user confirmation is needed"
    )


class FileSearchRequest(BaseModel):
    """Structured request for file search commands"""

    search_criteria: str = Field(description="What type of files to search for")
    directory: str = Field(default="Downloads", description="Directory to search in")
    action: str = Field(
        description="Action to perform (find largest, count, list, etc.)"
    )


# Pydantic AI Tools
def create_shell_command_tool() -> Tool:
    """Create a Pydantic AI tool for shell command generation"""

    async def generate_shell_command(
        request: Annotated[ShellCommandRequest, "Shell command generation request"],
    ) -> ShellCommandResponse:
        """Generate a safe and effective shell command based on user request"""

        user_request = request.user_request.lower()

        # Enhanced command generation logic
        if "find" in user_request and "largest" in user_request:
            if "downloads" in user_request:
                command = "find ~/Downloads -type f -print0 | xargs -0 du -h | sort -rh | head -n 1"
                explanation = (
                    "This command finds the largest file in Downloads directory. "
                    "It uses find to locate all files, du -h to get human-readable sizes, "
                    "sort -rh to sort by size (largest first), and head -n 1 to show only the top result. "
                    "The -print0 and xargs -0 options handle filenames with spaces safely."
                )
                safety_notes = [
                    "Command only reads file information, does not modify files"
                ]
            else:
                command = (
                    "find . -type f -print0 | xargs -0 du -h | sort -rh | head -n 1"
                )
                explanation = (
                    "This command finds the largest file in the current directory and subdirectories. "
                    "Uses find with du to calculate sizes, sorts by size, and shows the largest file."
                )
                safety_notes = [
                    "Searches current directory recursively",
                    "May take time in large directories",
                ]

        elif "list" in user_request and "file" in user_request:
            command = "ls -la"
            explanation = "Lists all files in the current directory with detailed information including permissions, size, and modification date."
            safety_notes = ["Read-only operation, safe to execute"]

        elif "disk" in user_request and (
            "usage" in user_request or "space" in user_request
        ):
            command = "df -h"
            explanation = (
                "Shows disk usage for all mounted filesystems in human-readable format."
            )
            safety_notes = ["Read-only operation showing system information"]

        else:
            # Fallback for complex requests
            command = f"# Complex request: {request.user_request}"
            explanation = "This request requires manual review. The command shown is a placeholder."
            safety_notes = [
                "Manual review required",
                "Command not automatically generated",
            ]

        return ShellCommandResponse(
            command=command,
            explanation=explanation,
            safety_notes=safety_notes,
            confidence=95.0,
            requires_confirmation=True,
        )

    return Tool(generate_shell_command, takes_ctx=False)


def create_file_search_tool() -> Tool:
    """Create a Pydantic AI tool for file search operations"""

    async def search_files(
        request: Annotated[FileSearchRequest, "File search request"],
    ) -> ShellCommandResponse:
        """Search for files based on specific criteria"""

        directory_map = {
            "downloads": "~/Downloads",
            "desktop": "~/Desktop",
            "documents": "~/Documents",
            "home": "~",
        }

        search_dir = directory_map.get(
            request.directory.lower(), f"~/{request.directory}"
        )

        if "largest" in request.action:
            command = f"find {search_dir} -type f -print0 | xargs -0 du -h | sort -rh | head -n 1"
            explanation = f"Finds the largest file in {search_dir} directory using find, du, and sort commands."
        elif "count" in request.action:
            command = f"find {search_dir} -type f | wc -l"
            explanation = f"Counts the total number of files in {search_dir} directory."
        elif "recent" in request.action:
            command = f"find {search_dir} -type f -mtime -7 -ls"
            explanation = (
                f"Lists files modified in the last 7 days in {search_dir} directory."
            )
        else:
            command = f"find {search_dir} -type f -name '*{request.search_criteria}*'"
            explanation = f"Searches for files containing '{request.search_criteria}' in their names within {search_dir}."

        return ShellCommandResponse(
            command=command,
            explanation=explanation,
            safety_notes=["Read-only file system operation", "Safe to execute"],
            confidence=90.0,
            requires_confirmation=True,
        )

    return Tool(search_files, takes_ctx=False)


async def execute_shell_command(command: str) -> dict[str, any]:
    """Execute a shell command and return results with timing"""
    start_time = datetime.now()

    try:
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        end_time = datetime.now()

        execution_time = (end_time - start_time).total_seconds()

        return {
            "success": process.returncode == 0,
            "stdout": stdout.decode("utf-8") if stdout else "",
            "stderr": stderr.decode("utf-8") if stderr else "",
            "return_code": process.returncode,
            "execution_time": f"{execution_time:.2f}s",
            "raw_output": (
                stdout.decode("utf-8")
                if stdout
                else stderr.decode("utf-8") if stderr else ""
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": 1,
            "execution_time": "0.00s",
            "raw_output": f"Error: {str(e)}",
        }

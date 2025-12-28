# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""GitHub Issue Function - Create GitHub issues with intelligent context gathering."""


import logging
from typing import Any, Dict, List

from ...core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
)

logger = logging.getLogger(__name__)


class GitHubIssueFunction(FunctionPlugin):
    """
    Create GitHub issues with intelligent context gathering (v0.4.10).

    Features:
    - Automatic repository context gathering (commits, issues, structure)
    - LLM-enhanced issue description with proper formatting
    - Label and assignee suggestions based on context
    - AII signature on created issues
    - Integration with MCP GitHub server
    """

    @property
    def name(self) -> str:
        return "github_issue"

    @property
    def description(self) -> str:
        return "Create a GitHub issue with intelligent context gathering and LLM enhancement"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def default_output_mode(self) -> OutputMode:
        return OutputMode.STANDARD

    @property
    def supports_output_modes(self) -> List[OutputMode]:
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.RISKY  # Creates external resource

    @property
    def requires_confirmation(self) -> bool:
        return True  # RISKY function requires confirmation

    def get_function_safety(self) -> FunctionSafety:
        return self.safety_level

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {}  # Legacy compatibility

    def get_parameters_schema(self) -> ParameterSchema:
        return {
            "type": "object",
            "properties": {
                "owner": {
                    "type": "string",
                    "description": "Repository owner (GitHub username or organization)"
                },
                "repo": {
                    "type": "string",
                    "description": "Repository name"
                },
                "title": {
                    "type": "string",
                    "description": "Issue title"
                },
                "body": {
                    "type": "string",
                    "description": "Issue description/body (will be enhanced with context)"
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Labels to add (optional, can be auto-suggested)",
                    "default": []
                },
                "assignees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Assignees (optional, can be auto-suggested)",
                    "default": []
                },
                "gather_context": {
                    "type": "boolean",
                    "description": "Gather repository context (commits, issues) for enhancement",
                    "default": True
                },
                "enhance_with_llm": {
                    "type": "boolean",
                    "description": "Use LLM to enhance issue description and suggest labels",
                    "default": True
                }
            },
            "required": ["owner", "repo", "title", "body"]
        }

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Create GitHub issue with intelligent context gathering."""
        try:
            owner = parameters["owner"]
            repo = parameters["repo"]
            title = parameters["title"]
            body = parameters["body"]
            labels = parameters.get("labels", [])
            assignees = parameters.get("assignees", [])
            gather_context = parameters.get("gather_context", True)
            enhance_with_llm = parameters.get("enhance_with_llm", True)

            # Check MCP client availability
            if not context.mcp_client:
                return ExecutionResult(
                    success=False,
                    message="GitHub MCP server not available. Run 'aii mcp add github' to set it up.",
                    data={"error": "mcp_not_available"}
                )

            # Step 1: Gather repository context (if enabled)
            repo_context = {}
            if gather_context:
                logger.info(f"Gathering context for {owner}/{repo}")
                repo_context = await self._gather_repository_context(
                    owner, repo, context.mcp_client
                )

            # Step 2: Enhance issue with LLM (if enabled and LLM available)
            enhanced_body = body
            suggested_labels = labels.copy()
            suggested_assignees = assignees.copy()

            if enhance_with_llm and context.llm_provider:
                logger.info("Enhancing issue with LLM")
                enhancement = await self._enhance_issue_with_llm(
                    title=title,
                    body=body,
                    repo_context=repo_context,
                    existing_labels=labels,
                    existing_assignees=assignees,
                    llm_provider=context.llm_provider
                )
                enhanced_body = enhancement["body"]
                suggested_labels = enhancement.get("labels", suggested_labels)
                suggested_assignees = enhancement.get("assignees", suggested_assignees)

            # Step 3: Add AII signature
            enhanced_body = self._add_aii_signature(enhanced_body)

            # Step 4: Create issue via MCP GitHub server
            logger.info(f"Creating issue '{title}' in {owner}/{repo}")
            issue_result = await self._create_issue_via_mcp(
                owner=owner,
                repo=repo,
                title=title,
                body=enhanced_body,
                labels=suggested_labels,
                assignees=suggested_assignees,
                mcp_client=context.mcp_client
            )

            if not issue_result["success"]:
                return ExecutionResult(
                    success=False,
                    message=f"Failed to create issue: {issue_result.get('error', 'Unknown error')}",
                    data=issue_result
                )

            issue_url = issue_result.get("url", f"https://github.com/{owner}/{repo}/issues")
            issue_number = issue_result.get("number", "?")

            return ExecutionResult(
                success=True,
                message=f"✅ Created issue #{issue_number}: {title}\n🔗 {issue_url}",
                data={
                    "clean_output": issue_url,
                    "issue_number": issue_number,
                    "issue_url": issue_url,
                    "title": title,
                    "labels": suggested_labels,
                    "assignees": suggested_assignees,
                    "context_gathered": gather_context,
                    "llm_enhanced": enhance_with_llm,
                    "repository": f"{owner}/{repo}"
                }
            )

        except Exception as e:
            logger.error(f"Error creating GitHub issue: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                message=f"Error creating GitHub issue: {str(e)}",
                data={"error": str(e)}
            )

    async def _gather_repository_context(
        self, owner: str, repo: str, mcp_client: Any
    ) -> Dict[str, Any]:
        """
        Gather repository context for issue enhancement.

        Context includes:
        - Recent commits (last 10)
        - Existing issues (last 20, with similar titles)
        - Project structure overview
        - Repository statistics
        """
        context = {
            "commits": [],
            "issues": [],
            "structure": {},
            "stats": {}
        }

        try:
            # Get recent commits via git (if in repo) or MCP
            # For now, use a simplified approach
            import subprocess

            # Check if we're in a git repository
            try:
                # Get last 10 commits
                result = subprocess.run(
                    ["git", "log", "--oneline", "-10"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    commits = result.stdout.strip().split("\n")
                    context["commits"] = [c.strip() for c in commits if c.strip()]
            except Exception:
                pass

            # Get repository statistics
            try:
                result = subprocess.run(
                    ["git", "rev-list", "--count", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    context["stats"]["total_commits"] = result.stdout.strip()
            except Exception:
                pass

            # Get basic project structure
            try:
                result = subprocess.run(
                    ["find", ".", "-type", "f", "-name", "*.py", "-o", "-name", "*.md", "|", "head", "-20"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split("\n")
                    context["structure"]["key_files"] = [f.strip() for f in files if f.strip()][:10]
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Error gathering repository context: {e}")

        return context

    async def _enhance_issue_with_llm(
        self,
        title: str,
        body: str,
        repo_context: Dict[str, Any],
        existing_labels: List[str],
        existing_assignees: List[str],
        llm_provider: Any
    ) -> Dict[str, Any]:
        """
        Use LLM to enhance issue description and suggest labels.

        Returns:
            Dictionary with enhanced body, suggested labels, and assignees
        """
        try:
            # Build context for LLM
            context_str = self._format_context_for_llm(repo_context)

            # Create LLM prompt
            prompt = f"""You are helping create a GitHub issue with intelligent context awareness.

**Issue Title:** {title}

**Original Description:**
{body}

**Repository Context:**
{context_str}

**Task:**
1. Enhance the issue description with:
   - Proper markdown formatting
   - Relevant context from recent commits/issues
   - Clear problem statement and expected behavior
   - Steps to reproduce (if applicable)
   - Additional relevant information

2. Suggest appropriate labels based on:
   - Issue content
   - Repository context
   - Common GitHub label conventions (bug, enhancement, documentation, etc.)

3. Keep the enhanced description concise but informative

**Current Labels:** {', '.join(existing_labels) if existing_labels else 'None'}

Respond in JSON format:
{{
  "body": "enhanced markdown body",
  "labels": ["label1", "label2"],
  "reasoning": "brief explanation of enhancements"
}}"""

            # Call LLM
            from pydantic_ai import Agent
            from pydantic import BaseModel

            class IssueEnhancement(BaseModel):
                body: str
                labels: List[str]
                reasoning: str

            agent = Agent(
                llm_provider.pydantic_model,
                result_type=IssueEnhancement,
                system_prompt="You are a helpful assistant that enhances GitHub issues with intelligent context."
            )

            result = await agent.run(prompt)
            enhancement_data = result.data

            return {
                "body": enhancement_data.body,
                "labels": list(set(existing_labels + enhancement_data.labels)),  # Merge with existing
                "assignees": existing_assignees,  # Keep existing assignees
                "reasoning": enhancement_data.reasoning
            }

        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}, using original content")
            return {
                "body": body,
                "labels": existing_labels,
                "assignees": existing_assignees,
                "reasoning": f"Enhancement skipped: {str(e)}"
            }

    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format repository context for LLM prompt."""
        parts = []

        if context.get("commits"):
            parts.append("**Recent Commits:**")
            for commit in context["commits"][:5]:
                parts.append(f"- {commit}")

        if context.get("stats"):
            parts.append("\n**Repository Stats:**")
            for key, value in context["stats"].items():
                parts.append(f"- {key}: {value}")

        if context.get("structure", {}).get("key_files"):
            parts.append("\n**Key Files:**")
            for file in context["structure"]["key_files"][:5]:
                parts.append(f"- {file}")

        return "\n".join(parts) if parts else "No context available"

    def _add_aii_signature(self, body: str) -> str:
        """Add AII signature to issue body."""
        signature = "\n\n---\n\n🤖 *Created with [AII](https://github.com/yourusername/aii) - AI-powered CLI assistant*"
        return body + signature

    async def _create_issue_via_mcp(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: List[str],
        assignees: List[str],
        mcp_client: Any
    ) -> Dict[str, Any]:
        """
        Create GitHub issue via MCP server.

        Returns:
            Dictionary with success status, issue number, and URL
        """
        try:
            # Call MCP GitHub server's create_issue tool
            tool_params = {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": body
            }

            # Add optional parameters if provided
            if labels:
                tool_params["labels"] = labels
            if assignees:
                tool_params["assignees"] = assignees

            result = await mcp_client.call_tool(
                server_name="github",
                tool_name="create_issue",
                arguments=tool_params
            )

            # Parse result
            if result.isError:
                return {
                    "success": False,
                    "error": str(result.content) if result.content else "Unknown error"
                }

            # Extract issue details from response
            # MCP result format varies, handle common patterns
            content = result.content[0].text if result.content else "{}"

            try:
                import json
                issue_data = json.loads(content) if isinstance(content, str) else content

                return {
                    "success": True,
                    "number": issue_data.get("number"),
                    "url": issue_data.get("html_url") or issue_data.get("url"),
                    "raw_response": issue_data
                }
            except Exception as parse_error:
                # Fallback: assume success if no error
                logger.warning(f"Could not parse issue response: {parse_error}")
                return {
                    "success": True,
                    "number": "?",
                    "url": f"https://github.com/{owner}/{repo}/issues",
                    "raw_response": str(content)
                }

        except Exception as e:
            logger.error(f"MCP call failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

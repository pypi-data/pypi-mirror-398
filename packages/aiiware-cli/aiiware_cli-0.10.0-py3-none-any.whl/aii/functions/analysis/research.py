# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Research Function - Research topics using web search and analysis."""


from pathlib import Path
from typing import Any

from ...cli.status_display import ProgressTracker
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


class ResearchFunction(FunctionPlugin):
    """Research topics using web search and analysis"""

    @property
    def name(self) -> str:
        return "research"

    @property
    def description(self) -> str:
        return (
            "Research topics using web search (news, articles, documentation) and provide comprehensive analysis. "
            "Use for: general knowledge queries, current events, technical concepts, product comparisons, industry trends. "
            "NOT for: GitHub repository searches (use mcp_tool for 'search repos', 'find repositories', 'popular repos')."
        )

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.ANALYSIS

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "query": ParameterSchema(
                name="query",
                type="string",
                required=True,
                description="Research query or topic",
            ),
            "depth": ParameterSchema(
                name="depth",
                type="string",
                required=False,
                description="Research depth",
                choices=["overview", "detailed", "comprehensive"],
                default="detailed",
            ),
            "sources": ParameterSchema(
                name="sources",
                type="integer",
                required=False,
                description="Number of sources to research",
                default=5,
            ),
        }

    @property
    def requires_confirmation(self) -> bool:
        return True  # Web search requires confirmation

    @property
    def safety_level(self) -> FunctionSafety:
        return FunctionSafety.SAFE

    @property
    def default_output_mode(self) -> OutputMode:
        """Research should show thinking mode by default (sources + reasoning)"""
        return OutputMode.THINKING

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Research supports all output modes"""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """Check prerequisites - only LLM provider is required, web search is optional"""
        errors = []

        if not context.llm_provider:
            errors.append("LLM provider required for research analysis")

        # Note: web_client is optional - we'll fall back to LLM-only mode if unavailable

        if errors:
            return ValidationResult(valid=False, errors=errors)

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute research with web search or LLM-only fallback"""
        query = parameters["query"]
        depth = parameters.get("depth", "detailed")
        max_sources = parameters.get("sources", 5)

        # Initialize progress tracker
        progress = ProgressTracker(use_emojis=True, use_animations=True)

        # Try web-based research first, fall back to LLM-only if unavailable
        use_web = context.web_client is not None
        web_attempted = use_web  # Track if we tried web search
        search_results = []

        # Define workflow steps based on mode
        if use_web:
            progress.add_step(f"Searching and analyzing sources", icon="🔍")
            progress.add_step("Synthesizing findings", icon="🤖")
        else:
            progress.add_step("Analyzing topic", icon="🤖")
            progress.add_step("Generating research report", icon="✨")

        step_index = 0

        if use_web:
            try:
                # Step 1: Search web sources
                progress.start_step(step_index)
                search_results = await context.web_client.search(
                    query, num_results=max_sources
                )

                if not search_results:
                    # No results found, fall back to LLM-only
                    progress.complete_step(step_index, success=False)
                    progress.finish()
                    use_web = False
                    # Restart with LLM-only mode
                    progress = ProgressTracker(use_emojis=True, use_animations=True)
                    progress.add_step("Analyzing topic", icon="🤖")
                    progress.add_step("Generating research report", icon="✨")
                    step_index = 0
                else:
                    progress.complete_step(step_index, success=True)
                    step_index += 1

            except Exception as e:
                # Web search failed (API error, network issue, etc.)
                # Fall back to LLM-only mode
                progress.complete_step(step_index, success=False)
                progress.finish()
                use_web = False
                # Restart with LLM-only mode
                progress = ProgressTracker(use_emojis=True, use_animations=True)
                progress.add_step("Analyzing topic", icon="🤖")
                progress.add_step("Generating research report", icon="✨")
                step_index = 0

        # Generate research report (web-based or LLM-only)
        try:
            if use_web and search_results:
                # Step 1 already completed (searching and analyzing)
                step_index += 1

                # Step 2: Synthesize findings
                progress.start_step(step_index)
                # CRITICAL: Stop progress animation before LLM streaming starts
                # Progress animation interferes with token-by-token streaming output
                progress._stop_animated_step()
                research_report, usage = await self._generate_research_report_with_web(
                    query, search_results, depth, context.llm_provider
                )
                research_mode = "web-based"
                progress.complete_step(step_index, success=True)
            else:
                # Step 1: Analyze topic (LLM-only)
                progress.start_step(step_index)
                progress.complete_step(step_index, success=True)
                step_index += 1

                # Step 2: Generate report
                progress.start_step(step_index)
                # CRITICAL: Stop progress animation before LLM streaming starts
                # Progress animation interferes with token-by-token streaming output
                progress._stop_animated_step()
                research_report, usage = await self._generate_research_report_llm_only(
                    query, depth, context.llm_provider
                )
                research_mode = "llm-only"
                search_results = []  # Ensure empty for consistency
                progress.complete_step(step_index, success=True)

            progress.finish()

            # Add helpful note for LLM-only mode
            message = f"# Research Report: {query}\n\n"
            if research_mode == "llm-only" and web_attempted:
                # Web was attempted but failed - inform user
                message += "💡 **Tip:** Web search failed (DuckDuckGo API unreliable). For web-based research:\n"
                message += "   1. Get free Brave Search API key: https://brave.com/search/api/\n"
                message += "   2. Add to `~/.aii/secrets.yaml`: `brave_api_key: your-key`\n"
                message += "   3. Update `~/.aii/config.yaml`: `web_search.provider: brave`\n\n"

            message += research_report

            # Create reasoning for THINKING mode
            reasoning_parts = [f"Researching '{query}'"]
            if research_mode == "web-based" and search_results:
                reasoning_parts.append(f"found {len(search_results)} sources")
            else:
                reasoning_parts.append("using LLM knowledge base")
            reasoning_parts.append(f"generating {depth} analysis")
            reasoning = ", ".join(reasoning_parts) + "."

            return ExecutionResult(
                success=True,
                message=message,
                data={
                    "clean_output": research_report,  # For CLEAN mode
                    "query": query,
                    "report": research_report,
                    "reasoning": reasoning,  # For THINKING/VERBOSE modes
                    "research_mode": research_mode,
                    "sources_found": len(search_results),
                    "input_tokens": usage.get("input_tokens", 0),
                    "output_tokens": usage.get("output_tokens", 0),
                    "reasoning_tokens": usage.get("reasoning_tokens", 0),
                    "depth": depth,
                    "sources": [
                        {"title": r.title, "url": r.url, "snippet": r.snippet}
                        for r in search_results
                    ] if search_results else [],
                },
            )

        except Exception as e:
            return ExecutionResult(success=False, message=f"Research failed: {str(e)}")

    async def _generate_research_report_with_web(
        self, query: str, search_results: Any, depth: str, llm_provider: Any
    ) -> tuple[str, dict[str, Any]]:
        """Generate comprehensive research report from web search results"""
        depth_instructions = {
            "overview": "Provide a high-level overview with key points",
            "detailed": "Provide detailed analysis with multiple perspectives",
            "comprehensive": "Provide comprehensive analysis with deep insights and implications",
        }

        depth_instruction = depth_instructions.get(
            depth, depth_instructions["detailed"]
        )

        # Compile search results
        sources_text = "\n\n".join(
            [
                f"**Source {i+1}: {result.title}**\n{result.snippet}\nURL: {result.url}"
                for i, result in enumerate(search_results[:5])
            ]
        )

        # Enhanced prompt with better synthesis instructions
        prompt = f"""You are a research analyst tasked with synthesizing information from multiple web sources.

**Research Topic:** {query}

**Available Sources:**
{sources_text}

**Your Task:**
Create a comprehensive, well-synthesized research report that:
- {depth_instruction}
- Synthesizes information across all sources (don't just summarize each source separately)
- Identifies key themes, patterns, and consensus viewpoints
- Highlights any conflicting information or different perspectives
- Includes current trends and recent developments
- Provides balanced analysis on controversial topics
- Cites sources inline using [Source N] format
- Uses clear markdown structure with headings and sections

**Report Structure:**

## Executive Summary
Brief 2-3 sentence overview of the topic and key findings.

## Key Findings
- Bullet points of the most important discoveries
- Each point should synthesize information from multiple sources
- Cite sources: [Source 1], [Source 2], etc.

## Current State and Trends
Detailed analysis of the current landscape and emerging trends. Synthesize cross-source information.

## Different Perspectives
(If applicable) Present varying viewpoints or debates on the topic with source citations.

## Implications and Impact
Analyze the significance and potential consequences. What does this mean for stakeholders?

## Future Outlook
Based on the sources, what are the predicted developments or areas to watch?

## Sources and References
{chr(10).join([f"[Source {i+1}] {result.title} - {result.url}" for i, result in enumerate(search_results)])}

Generate the research report following the structure above:"""

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Use complete_with_usage to track token consumption
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                usage = {}

            return (
                str(result) if result is not None else "Failed to generate research report",
                usage
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate research report: {str(e)}") from e

    async def _generate_research_report_llm_only(
        self, query: str, depth: str, llm_provider: Any
    ) -> tuple[str, dict[str, Any]]:
        """Generate research report using only LLM knowledge (fallback when web unavailable)"""
        depth_instructions = {
            "overview": "Provide a high-level overview with key points from your knowledge",
            "detailed": "Provide detailed analysis based on your training data",
            "comprehensive": "Provide comprehensive analysis with deep insights from your knowledge base",
        }

        depth_instruction = depth_instructions.get(
            depth, depth_instructions["detailed"]
        )

        prompt = f"""You are a knowledgeable research analyst. Web search is currently unavailable, so provide a research report based on your training data and knowledge.

**Research Topic:** {query}

**Your Task:**
Create a well-structured research report based on your knowledge that:
- {depth_instruction}
- Clearly indicates this is based on your training data (knowledge cutoff: January 2025)
- Highlights what information might be outdated or require current sources
- Provides balanced analysis when discussing controversial topics
- Uses clear markdown structure with headings and sections
- Notes where web sources would provide more current information

**Report Structure:**

## Executive Summary
Brief 2-3 sentence overview of the topic based on your knowledge.

## Key Concepts and Background
Core information about the topic from your training data.

## Known Developments (as of training cutoff)
What you know about this topic up to January 2025.

## Limitations of This Analysis
Explicitly state:
- This analysis is based on training data (knowledge cutoff: January 2025)
- Areas where current web sources would provide more up-to-date information
- Topics that may have evolved significantly since your training

## Recommendations
Suggest areas where the user should seek current sources for the most accurate information.

**Note:** Please start your response with a clear disclaimer: "⚠️ LLM-Only Mode: This research is based on training data (knowledge cutoff: January 2025) without current web sources."

Generate the research report following the structure above:"""

        try:
            # Get streaming callback if available
            streaming_callback = getattr(llm_provider, '_streaming_callback', None)

            # Use complete_with_usage to track token consumption
            if hasattr(llm_provider, "complete_with_usage"):
                llm_response = await llm_provider.complete_with_usage(
                    prompt,
                    on_token=streaming_callback
                )
                result = llm_response.content
                usage = llm_response.usage or {}
            else:
                result = await llm_provider.complete(prompt)
                usage = {}

            return (
                str(result) if result is not None else "Failed to generate research report",
                usage
            )
        except Exception as e:
            raise RuntimeError(f"Failed to generate LLM-only research report: {str(e)}") from e

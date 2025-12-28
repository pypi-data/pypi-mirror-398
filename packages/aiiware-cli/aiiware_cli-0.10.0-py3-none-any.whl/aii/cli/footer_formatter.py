# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Session Footer Formatter for comprehensive session metrics display"""


from typing import List, Optional
from enum import Enum
import asyncio
import time

from ..core.session.models import SessionMetrics
from ..core.session.semantic_analyzer import SessionSemanticAnalyzer, SessionInsights
from ..core.performance import performance_timed


class VerbosityLevel(Enum):
    """Output verbosity levels"""
    MINIMAL = 1
    STANDARD = 2
    DETAILED = 3


class SessionFooterFormatter:
    """Formats session footers with structured metrics based on verbosity level"""

    def __init__(self, use_colors: bool = True, use_emojis: bool = True,
                 semantic_analyzer: Optional[SessionSemanticAnalyzer] = None):
        self.use_colors = use_colors
        self.use_emojis = use_emojis
        self.semantic_analyzer = semantic_analyzer

        # Color codes for terminal output
        self.color_codes = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "red": "\033[31m",
            "bright_green": "\033[92m",
            "bright_yellow": "\033[93m",
            "bright_blue": "\033[94m",
            "bright_red": "\033[91m",
        }

        # Emoji mappings
        self.emoji_map = {
            "summary": "📊",
            "time": "⚡",
            "tokens": "🔢",
            "artifacts": "📦",
            "functions": "🔧",
            "performance": "📈",
            "quality": "🏆",
            "session": "🏁",
            "cost": "💰",
            "success": "✅",
            "partial": "⚠️",
            "failed": "❌",
            "achievement": "🎯",
        }

    @performance_timed("footer_formatter.format_session_footer")
    def format_session_footer(self, session: SessionMetrics,
                             verbosity: VerbosityLevel = VerbosityLevel.STANDARD,
                             total_duration: float = None) -> str:
        """Generate footer from accumulated session data (synchronous version)"""
        if not session:
            return self._format_empty_footer()

        if verbosity == VerbosityLevel.MINIMAL:
            return self._format_minimal_footer(session, total_duration)
        elif verbosity == VerbosityLevel.STANDARD:
            return self._format_standard_footer(session, total_duration)
        else:  # VerbosityLevel.DETAILED
            return self._format_detailed_footer(session, total_duration)

    @performance_timed("footer_formatter.format_intelligent_footer")
    async def format_intelligent_footer(self, session: SessionMetrics, user_input: str,
                                       verbosity: VerbosityLevel = VerbosityLevel.STANDARD,
                                       total_duration: float = None) -> str:
        """Generate footer with optional semantic analysis based on verbosity"""
        if not session:
            return self._format_empty_footer()

        # Conditional semantic analysis based on verbosity and analyzer availability
        insights = None
        if self.semantic_analyzer and verbosity.value >= VerbosityLevel.STANDARD.value:
            try:
                # Measure semantic analysis performance
                analysis_start = time.time()
                insights = await self.semantic_analyzer.analyze_session_outcomes(
                    user_input, session
                )
                analysis_time = time.time() - analysis_start

                # Log performance (only for detailed verbosity)
                if verbosity == VerbosityLevel.DETAILED and analysis_time > 2.0:
                    print(f"⚠️ Semantic analysis took {analysis_time:.1f}s (target: <2s)")

            except Exception as e:
                # Fall back to structured-only footer on LLM failure
                if verbosity == VerbosityLevel.DETAILED:
                    print(f"⚠️ Semantic analysis failed: {str(e)[:50]}... (using structured metrics)")

        # Generate footer based on available data
        return self._compose_footer_with_insights(session, insights, verbosity, total_duration)

    def _format_minimal_footer(self, session: SessionMetrics, total_duration: float = None) -> str:
        """Minimal: Just time, tokens, success status"""
        summary_icon = self._get_icon("summary")

        # Time and tokens
        duration = session.session_duration
        total_tokens = session.total_tokens

        # Status with color
        if session.success_rate == 1.0:
            status_icon = self._get_icon("success")
            status_text = f"{status_icon} Success"
            if session.total_functions > 1:
                status_text += f" ({session.total_functions}/{session.total_functions})"
        elif session.success_rate > 0:
            status_icon = self._get_icon("partial")
            status_text = f"{status_icon} Partial ({session.successful_functions}/{session.total_functions})"
        else:
            status_icon = self._get_icon("failed")
            status_text = f"{status_icon} Failed"

        return f"{summary_icon} {duration:.1f}s • {total_tokens} tokens • {status_text}"

    def _format_standard_footer(self, session: SessionMetrics, total_duration: float = None) -> str:
        """Standard: Add function breakdown and artifacts"""
        lines = []

        # Header (with blank line above for better readability)
        summary_icon = self._get_icon("summary")
        lines.append(f"\n{summary_icon} Session Summary:")

        # Timing, tokens, and cost
        time_icon = self._get_icon("time")
        tokens_icon = self._get_icon("tokens")

        input_and_reasoning = session.total_input_tokens + session.total_reasoning_tokens

        # Show both processing time and total time if available
        if total_duration is not None and total_duration > session.session_duration + 0.5:
            # Show both times if total is significantly larger (>0.5s difference)
            timing_tokens_line = (
                f"{time_icon} Processing: {session.session_duration:.1f}s • Total: {total_duration:.1f}s • "
                f"{tokens_icon} Tokens: {input_and_reasoning}↗ {session.total_output_tokens}↘ "
                f"({session.total_tokens} total)"
            )
        else:
            # Show only session time if they're close
            timing_tokens_line = (
                f"{time_icon} Total time: {session.session_duration:.1f}s • "
                f"{tokens_icon} Tokens: {input_and_reasoning}↗ {session.total_output_tokens}↘ "
                f"({session.total_tokens} total)"
            )

        # Add cost information if available
        if session.total_cost > 0:
            cost_icon = self._get_icon("cost")
            cost_str = self._format_cost(session.total_cost)
            timing_tokens_line += f" • {cost_icon} {cost_str}"

        lines.append(timing_tokens_line)

        # Artifacts created
        if session.artifacts_created:
            artifacts_icon = self._get_icon("artifacts")
            primary_artifacts = session.artifacts_created[:3]  # Show top 3
            artifacts_line = f"{artifacts_icon} Created: {', '.join(primary_artifacts)}"
            if len(session.artifacts_created) > 3:
                artifacts_line += f" (+{len(session.artifacts_created) - 3} more)"
            lines.append(artifacts_line)

        # Success status
        if session.success_rate == 1.0:
            success_icon = self._get_icon("success")
            lines.append(f"{success_icon} Pipeline completed successfully ({session.total_functions} functions)")
        elif session.success_rate > 0:
            partial_icon = self._get_icon("partial")
            lines.append(f"{partial_icon} Partial success: {session.successful_functions}/{session.total_functions} functions completed")
        else:
            failed_icon = self._get_icon("failed")
            lines.append(f"{failed_icon} Pipeline failed: 0/{session.total_functions} functions completed")

        return "\n".join(lines)

    def _format_detailed_footer(self, session: SessionMetrics, total_duration: float = None) -> str:
        """Detailed: Full breakdown with performance metrics"""
        lines = []

        # Header
        summary_icon = self._get_icon("summary")
        lines.append(f"{summary_icon} Session Summary:")

        # Core metrics with cost tracking
        time_icon = self._get_icon("time")
        tokens_icon = self._get_icon("tokens")

        input_and_reasoning = session.total_input_tokens + session.total_reasoning_tokens
        core_metrics_line = (
            f"{time_icon} Total time: {session.session_duration:.1f}s • "
            f"{tokens_icon} Tokens: {input_and_reasoning}↗ {session.total_output_tokens}↘ "
            f"({session.total_tokens} total)"
        )

        # Add cost information if available
        if session.total_cost > 0:
            cost_icon = self._get_icon("cost")
            cost_str = self._format_cost(session.total_cost)
            core_metrics_line += f" • {cost_icon} Cost: {cost_str}"

        lines.append(core_metrics_line)

        # Function pipeline breakdown
        if session.function_executions:
            functions_icon = self._get_icon("functions")
            function_names = [exec.function_name for exec in session.function_executions]
            lines.append(f"{functions_icon} Functions: {' → '.join(function_names)}")

        # Performance metrics
        if session.total_functions > 0:
            performance_icon = self._get_icon("performance")
            avg_function_time = session.average_function_time
            avg_tokens_per_function = session.total_tokens // session.total_functions
            lines.append(
                f"{performance_icon} Performance: avg {avg_function_time:.1f}s/function • "
                f"{avg_tokens_per_function} tokens/function"
            )

        # Artifacts created (detailed list)
        if session.artifacts_created:
            artifacts_icon = self._get_icon("artifacts")
            if len(session.artifacts_created) <= 5:
                artifacts_line = f"{artifacts_icon} Artifacts: {', '.join(session.artifacts_created)}"
            else:
                primary_artifacts = session.artifacts_created[:5]
                artifacts_line = f"{artifacts_icon} Artifacts: {', '.join(primary_artifacts)} (+{len(session.artifacts_created) - 5} more)"
            lines.append(artifacts_line)

        # Quality assessment
        quality_icon = self._get_icon("quality")
        if session.success_rate == 1.0:
            quality_text = "Excellent"
        elif session.success_rate >= 0.8:
            quality_text = "Good"
        elif session.success_rate >= 0.5:
            quality_text = "Partial"
        else:
            quality_text = "Poor"

        confidence_info = ""
        if session.function_executions:
            confidences = [exec.confidence for exec in session.function_executions if exec.confidence is not None]
            if confidences:
                # Normalize confidence values to percentage scale (handle both 0-1 and 0-100 formats)
                normalized_confidences = []
                for conf in confidences:
                    if conf <= 1.0:
                        # 0-1 scale, convert to percentage
                        normalized_confidences.append(conf * 100)
                    else:
                        # Already percentage scale
                        normalized_confidences.append(conf)

                avg_confidence = sum(normalized_confidences) / len(normalized_confidences)
                confidence_info = f" • Avg confidence: {avg_confidence:.1f}%"

        lines.append(f"{quality_icon} Quality: {quality_text} - {session.successful_functions}/{session.total_functions} functions successful{confidence_info}")

        # Session info
        session_icon = self._get_icon("session")
        short_session_id = self._shorten_session_id(session.session_id)
        lines.append(f"{session_icon} Session: {short_session_id}")

        return "\n".join(lines)

    def _compose_footer_with_insights(self, session: SessionMetrics,
                                     insights: Optional[SessionInsights],
                                     verbosity: VerbosityLevel,
                                     total_duration: float = None) -> str:
        """Compose footer with semantic insights integration"""
        if verbosity == VerbosityLevel.MINIMAL:
            return self._format_minimal_footer(session, total_duration)
        elif verbosity == VerbosityLevel.STANDARD:
            return self._format_standard_footer_with_insights(session, insights, total_duration)
        else:  # VerbosityLevel.DETAILED
            return self._format_detailed_footer_with_insights(session, insights, total_duration)

    def _format_standard_footer_with_insights(self, session: SessionMetrics,
                                             insights: Optional[SessionInsights],
                                             total_duration: float = None) -> str:
        """Standard footer enhanced with semantic insights"""
        lines = []

        # Header (with blank line above for better readability)
        summary_icon = self._get_icon("summary")
        lines.append(f"\n{summary_icon} Session Summary:")

        # Core metrics
        time_icon = self._get_icon("time")
        tokens_icon = self._get_icon("tokens")
        input_and_reasoning = session.total_input_tokens + session.total_reasoning_tokens

        # Show both processing time and total time if available
        if total_duration is not None and total_duration > session.session_duration + 0.5:
            timing_tokens_line = (
                f"{time_icon} Processing: {session.session_duration:.1f}s • Total: {total_duration:.1f}s • "
                f"{tokens_icon} Tokens: {input_and_reasoning}↗ {session.total_output_tokens}↘ "
                f"({session.total_tokens} total)"
            )
        else:
            timing_tokens_line = (
                f"{time_icon} Total time: {session.session_duration:.1f}s • "
                f"{tokens_icon} Tokens: {input_and_reasoning}↗ {session.total_output_tokens}↘ "
                f"({session.total_tokens} total)"
            )

        # Add cost information if available
        if session.total_cost > 0:
            cost_icon = self._get_icon("cost")
            cost_str = self._format_cost(session.total_cost)
            timing_tokens_line += f" • {cost_icon} {cost_str}"

        lines.append(timing_tokens_line)

        # Semantic insights - SESSION SUMMARY
        if insights and insights.session_summary:
            achievement_icon = self._get_icon("achievement")
            lines.append(f"{achievement_icon} Accomplished: {insights.session_summary}")

        # Artifacts created (use session artifacts since insights doesn't track artifacts)
        artifacts_to_show = []
        if session.artifacts_created:
            artifacts_to_show = session.artifacts_created[:3]

        if artifacts_to_show:
            artifacts_icon = self._get_icon("artifacts")
            artifacts_line = f"{artifacts_icon} Created: {', '.join(artifacts_to_show)}"
            lines.append(artifacts_line)

        # Success status with semantic quality insight
        if session.success_rate == 1.0:
            success_icon = self._get_icon("success")
            status_line = f"{success_icon} Pipeline completed successfully ({session.total_functions} functions)"
            if insights and insights.function_efficiency and insights.function_efficiency != "excellent":
                status_line += f" • Efficiency: {insights.function_efficiency.title()}"
        elif session.success_rate > 0:
            partial_icon = self._get_icon("partial")
            status_line = f"{partial_icon} Partial success: {session.successful_functions}/{session.total_functions} functions completed"
        else:
            failed_icon = self._get_icon("failed")
            status_line = f"{failed_icon} Pipeline failed"

        lines.append(status_line)

        return "\n".join(lines)

    def _format_detailed_footer_with_insights(self, session: SessionMetrics,
                                             insights: Optional[SessionInsights],
                                             total_duration: float = None) -> str:
        """Detailed footer with full semantic insights integration"""
        lines = []

        # Header
        summary_icon = self._get_icon("summary")
        lines.append(f"{summary_icon} Session Summary:")

        # Core metrics with cost tracking
        time_icon = self._get_icon("time")
        tokens_icon = self._get_icon("tokens")

        input_and_reasoning = session.total_input_tokens + session.total_reasoning_tokens
        core_metrics_line = (
            f"{time_icon} Total time: {session.session_duration:.1f}s • "
            f"{tokens_icon} Tokens: {input_and_reasoning}↗ {session.total_output_tokens}↘ "
            f"({session.total_tokens} total)"
        )

        # Add cost information if available
        if session.total_cost > 0:
            cost_icon = self._get_icon("cost")
            cost_str = self._format_cost(session.total_cost)
            core_metrics_line += f" • {cost_icon} Cost: {cost_str}"

        lines.append(core_metrics_line)

        # SESSION SUMMARY from semantic analysis
        if insights and insights.session_summary:
            achievement_icon = self._get_icon("achievement")
            lines.append(f"{achievement_icon} Primary Achievement: {insights.session_summary}")

        # ARTIFACTS with semantic enhancement
        artifacts_to_show = []
        if session.artifacts_created:
            artifacts_to_show = session.artifacts_created

        if artifacts_to_show:
            artifacts_icon = self._get_icon("artifacts")
            if len(artifacts_to_show) <= 5:
                artifacts_line = f"{artifacts_icon} Artifacts: {', '.join(artifacts_to_show)}"
            else:
                primary_artifacts = artifacts_to_show[:5]
                artifacts_line = f"{artifacts_icon} Artifacts: {', '.join(primary_artifacts)} (+{len(artifacts_to_show) - 5} more)"
            lines.append(artifacts_line)

        # Function pipeline
        if session.function_executions:
            functions_icon = self._get_icon("functions")
            function_names = [exec.function_name for exec in session.function_executions]
            lines.append(f"{functions_icon} Functions: {' → '.join(function_names)}")

        # Performance metrics with semantic efficiency note
        if session.total_functions > 0:
            performance_icon = self._get_icon("performance")
            avg_function_time = session.average_function_time
            avg_tokens_per_function = session.total_tokens // session.total_functions
            perf_line = (
                f"{performance_icon} Performance: avg {avg_function_time:.1f}s/function • "
                f"{avg_tokens_per_function} tokens/function"
            )

            # Add semantic efficiency insight if available
            if insights and insights.token_efficiency:
                perf_line += f" • Token efficiency: {insights.token_efficiency}"

            lines.append(perf_line)

        # QUALITY assessment with semantic insights
        quality_icon = self._get_icon("quality")

        # Use semantic quality if available, otherwise compute from success rate
        if insights and insights.function_efficiency:
            quality_text = insights.function_efficiency.title()
        else:
            if session.success_rate == 1.0:
                quality_text = "Excellent"
            elif session.success_rate >= 0.8:
                quality_text = "Good"
            elif session.success_rate >= 0.5:
                quality_text = "Partial"
            else:
                quality_text = "Poor"

        confidence_info = ""
        if session.function_executions:
            confidences = [exec.confidence for exec in session.function_executions if exec.confidence is not None]
            if confidences:
                # Normalize confidence values to percentage scale (handle both 0-1 and 0-100 formats)
                normalized_confidences = []
                for conf in confidences:
                    if conf <= 1.0:
                        # 0-1 scale, convert to percentage
                        normalized_confidences.append(conf * 100)
                    else:
                        # Already percentage scale
                        normalized_confidences.append(conf)

                avg_confidence = sum(normalized_confidences) / len(normalized_confidences)
                confidence_info = f" • Avg confidence: {avg_confidence:.1f}%"

        # Add semantic user satisfaction if available
        quality_line = f"{quality_icon} Quality: {quality_text} - {session.successful_functions}/{session.total_functions} functions successful{confidence_info}"
        if insights and insights.user_satisfaction_estimate:
            satisfaction_pct = insights.user_satisfaction_estimate * 100
            quality_line += f" • User satisfaction: {satisfaction_pct:.0f}%"

        lines.append(quality_line)

        # Session info
        session_icon = self._get_icon("session")
        short_session_id = self._shorten_session_id(session.session_id)
        lines.append(f"{session_icon} Session: {short_session_id}")

        return "\n".join(lines)

    def _format_empty_footer(self) -> str:
        """Fallback footer when no session data available"""
        summary_icon = self._get_icon("summary")
        failed_icon = self._get_icon("failed")
        return f"{summary_icon} {failed_icon} No session data available"


    def _shorten_session_id(self, session_id: str) -> str:
        """Shorten session ID for display"""
        if "_" in session_id:
            return session_id.split("_")[-1][:8]
        return session_id[:8]

    def _get_icon(self, icon_type: str) -> str:
        """Get emoji icon or fallback text"""
        if self.use_emojis and icon_type in self.emoji_map:
            return self.emoji_map[icon_type]

        # Fallback text for non-emoji environments
        fallbacks = {
            "summary": "[SUMMARY]",
            "time": "[TIME]",
            "tokens": "[TOKENS]",
            "artifacts": "[ARTIFACTS]",
            "functions": "[FUNCTIONS]",
            "performance": "[PERF]",
            "quality": "[QUALITY]",
            "session": "[SESSION]",
            "cost": "[COST]",
            "success": "[OK]",
            "partial": "[PARTIAL]",
            "failed": "[FAILED]",
            "achievement": "[ACHIEVEMENT]",
        }
        return fallbacks.get(icon_type, "[INFO]")

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled"""
        if not self.use_colors or color not in self.color_codes:
            return text
        return f"{self.color_codes[color]}{text}{self.color_codes['reset']}"

    def _format_cost(self, amount: float) -> str:
        """Format cost amount for display"""
        if amount == 0.0:
            return "$0.00"
        elif amount < 0.001:
            return f"${amount:.6f}"
        elif amount < 0.01:
            return f"${amount:.4f}"
        else:
            return f"${amount:.2f}"

    def display_footer(self, footer_text: str) -> None:
        """Display formatted footer to console"""
        print(footer_text)

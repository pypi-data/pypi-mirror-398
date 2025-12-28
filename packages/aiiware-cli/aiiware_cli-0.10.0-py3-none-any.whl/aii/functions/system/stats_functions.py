# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Statistics and analytics functions for usage insights."""


from typing import Any, Dict
from pathlib import Path

from aii.core.models import (
    ExecutionContext,
    ExecutionResult,
    FunctionCategory,
    FunctionPlugin,
    FunctionSafety,
    OutputMode,
    ParameterSchema,
    ValidationResult,
)
from aii.data.storage.analytics import SessionAnalytics


class StatsFunction(FunctionPlugin):
    """Show usage statistics and insights from command history."""

    @property
    def name(self) -> str:
        return "stats"

    @property
    def description(self) -> str:
        return "Show usage statistics and insights from command history (function usage, token consumption, cost breakdown)"

    @property
    def category(self) -> FunctionCategory:
        return FunctionCategory.SYSTEM

    @property
    def parameters(self) -> dict[str, ParameterSchema]:
        return {
            "period": ParameterSchema(
                name="period",
                type="string",
                required=False,
                default="30d",
                description="Time period for statistics (7d, 30d, 90d, all)",
            ),
            "breakdown": ParameterSchema(
                name="breakdown",
                type="string",
                required=False,
                default="all",
                description="Type of breakdown to show (functions, tokens, cost, all)",
            ),
            "exclude_stats": ParameterSchema(
                name="exclude_stats",
                type="boolean",
                required=False,
                default=False,
                description="Exclude stats function from results to avoid observer effect",
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
        """Default to CLEAN mode - users want formatted stats."""
        return OutputMode.CLEAN

    @property
    def supports_output_modes(self) -> list[OutputMode]:
        """Supports all output modes."""
        return [OutputMode.CLEAN, OutputMode.STANDARD, OutputMode.THINKING]

    async def validate_prerequisites(
        self, context: ExecutionContext
    ) -> ValidationResult:
        """No prerequisites needed for stats"""
        return ValidationResult(valid=True)

    async def execute(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """Execute stats analysis.

        Args:
            parameters: Period and breakdown filters
            context: Execution context

        Returns:
            ExecutionResult with usage statistics
        """
        period = parameters.get("period", "30d")
        breakdown = parameters.get("breakdown", "all")
        exclude_stats = parameters.get("exclude_stats", False)

        try:
            # Create analytics instance
            analytics = SessionAnalytics()

            # Query analytics
            stats = await analytics.get_usage_stats(period, breakdown)

            # Filter out stats function if requested
            if exclude_stats and "functions" in stats:
                func_data = stats["functions"]
                # Filter out stats from by_function list (list of tuples)
                func_data["by_function"] = [
                    (name, count) for name, count in func_data.get("by_function", [])
                    if name != "stats"
                ]
                # Recalculate total executions
                func_data["total_executions"] = sum(
                    count for _, count in func_data["by_function"]
                )
                # Update total_sessions to match filtered executions
                stats["total_sessions"] = func_data["total_executions"]

            # Format output
            formatted = self._format_stats(stats, period, breakdown)

            # Create reasoning for THINKING/VERBOSE modes
            total_sessions = stats.get("total_sessions", 0)
            period_description = {"7d": "7 days", "30d": "30 days", "90d": "90 days", "all": "all time"}.get(period, period)
            reasoning = f"Analyzed {total_sessions} command execution(s) from the last {period_description}, aggregating function usage, token consumption, and cost metrics from the local analytics database"

            return ExecutionResult(
                success=True,
                message=f"Usage statistics for last {period}",
                data={
                    "stats": stats,
                    "period": period,
                    "breakdown": breakdown,
                    "clean_output": formatted,
                    "reasoning": reasoning,  # For THINKING/VERBOSE modes
                }
            )

        except ValueError as e:
            return ExecutionResult(
                success=False,
                message=f"Invalid parameter: {str(e)}",
                data={
                    "error": str(e),
                    "clean_output": f"Error: {str(e)}"
                }
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Error generating statistics: {str(e)}",
                data={
                    "error": str(e),
                    "clean_output": f"Error: {str(e)}"
                }
            )

    def _format_stats(
        self,
        stats: Dict[str, Any],
        period: str,
        breakdown: str
    ) -> str:
        """Format statistics for display.

        Args:
            stats: Statistics dictionary
            period: Time period
            breakdown: Breakdown type

        Returns:
            Formatted string for display
        """
        output = [f"📊 AII Usage Statistics (Last {period})\n"]

        # Session summary
        total_sessions = stats.get("total_sessions", 0)
        output.append(f"Total Executions: {total_sessions}")

        if total_sessions == 0:
            output.append("\nNo usage data available for this period.")
            return "\n".join(output)

        output.append("")  # Blank line

        # Function breakdown
        if "functions" in stats:
            functions = stats["functions"]
            output.append("📈 Top Functions:")

            total_executions = functions.get("total_executions", 0)
            for func_name, count in functions.get("by_function", [])[:5]:
                percentage = (count / total_executions * 100) if total_executions > 0 else 0
                output.append(f"  {count:3d}× {func_name:20s} ({percentage:.1f}%)")

            if len(functions.get("by_function", [])) > 5:
                remaining = len(functions.get("by_function", [])) - 5
                output.append(f"  ... and {remaining} more")

            output.append("")

        # Token breakdown
        if "tokens" in stats:
            tokens = stats["tokens"]
            total_tokens = tokens.get("total_tokens", 0)

            if total_tokens > 0:
                output.append("🔢 Token Usage:")
                output.append(f"  Total: {total_tokens:,} tokens")
                output.append(f"  Input: {tokens.get('total_input', 0):,} tokens")
                output.append(f"  Output: {tokens.get('total_output', 0):,} tokens")
                output.append("")

        # Cost breakdown
        if "costs" in stats:
            costs = stats["costs"]
            total_cost = costs.get("total_cost", 0.0)

            if total_cost > 0:
                output.append("💰 Cost Breakdown:")
                output.append(f"  Total: ${total_cost:.4f}\n")

                by_function = costs.get("by_function", [])
                if by_function:
                    output.append("  Top 5 by cost:")
                    for func_name, cost in by_function[:5]:
                        percentage = (cost / total_cost * 100) if total_cost > 0 else 0
                        output.append(f"    {func_name:20s} ${cost:.4f} ({percentage:.1f}%)")

                    if len(by_function) > 5:
                        remaining = len(by_function) - 5
                        output.append(f"  ... and {remaining} more")

        return "\n".join(output)

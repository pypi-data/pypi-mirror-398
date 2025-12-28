# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Model performance statistics function - Analyze model execution metrics."""


import json
from pathlib import Path
from typing import Any, Dict

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
from aii.data.analytics.model_performance_analyzer import ModelPerformanceAnalyzer


class StatsModelsFunction(FunctionPlugin):
    """Show model performance statistics - success rates, latency, tokens, cost.

    IMPORTANT: This function reads cost_usd from the database.
    It NEVER recalculates cost from tokens. Cost is calculated once by
    CostCalculator in executor.py and stored in the database as the single source of truth.
    """

    @property
    def name(self) -> str:
        return "stats_models"

    @property
    def description(self) -> str:
        return "Show model performance statistics including success rates, average latency (TTFT, total time), token usage, and cost analysis across all LLM providers"

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
            "category": ParameterSchema(
                name="category",
                type="string",
                required=False,
                default=None,
                description="Filter by function category (translation, analysis, code_operations, etc.)",
            ),
            "format": ParameterSchema(
                name="format",
                type="string",
                required=False,
                default="table",
                description="Output format (table or json)",
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
        """Check if database exists."""
        # Database path from engine's storage path
        db_path = Path.home() / ".aii" / "chats.db"

        if not db_path.exists():
            return ValidationResult(
                valid=False,
                error_message="No analytics data available. Database not found.",
            )

        return ValidationResult(valid=True)

    async def execute(
        self, parameters: Dict[str, Any], context: ExecutionContext
    ) -> ExecutionResult:
        """Execute model performance analysis.

        Args:
            parameters: Period, category filter, format
            context: Execution context

        Returns:
            ExecutionResult with model performance statistics
        """
        period = parameters.get("period", "30d")
        category = parameters.get("category", None)
        output_format = parameters.get("format", "table")

        # Validate period
        valid_periods = ["7d", "30d", "90d", "all"]
        if period not in valid_periods:
            return ExecutionResult(
                success=False,
                message=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}",
                data={"error": f"Invalid period: {period}"},
            )

        # Validate format
        valid_formats = ["table", "json"]
        if output_format not in valid_formats:
            return ExecutionResult(
                success=False,
                message=f"Invalid format '{output_format}'. Must be one of: {', '.join(valid_formats)}",
                data={"error": f"Invalid format: {output_format}"},
            )

        try:
            # Get database path
            db_path = Path.home() / ".aii" / "chats.db"

            # Create analyzer
            analyzer = ModelPerformanceAnalyzer(db_path, cache_ttl_seconds=60)

            # Get model performance data
            models = await analyzer.get_model_performance(
                period=period, category=category, use_cache=True
            )

            if not models:
                period_desc = {
                    "7d": "7 days",
                    "30d": "30 days",
                    "90d": "90 days",
                    "all": "all time",
                }.get(period, period)
                category_desc = f" in category '{category}'" if category else ""

                return ExecutionResult(
                    success=True,
                    message=f"No model performance data available for last {period_desc}{category_desc}",
                    data={
                        "models": [],
                        "period": period,
                        "category": category,
                        "clean_output": f"No model performance data available for last {period_desc}{category_desc}.",
                    },
                )

            # Format output
            if output_format == "json":
                # JSON format
                json_data = [
                    {
                        "model": m.model,
                        "provider": m.provider,
                        "total_executions": m.total_executions,
                        "successful_executions": m.successful_executions,
                        "failed_executions": m.failed_executions,
                        "success_rate": m.success_rate,
                        "avg_ttft_ms": m.avg_ttft_ms,
                        "avg_execution_time_ms": m.avg_execution_time_ms,
                        "total_input_tokens": m.total_input_tokens,
                        "total_output_tokens": m.total_output_tokens,
                        "avg_input_tokens": m.avg_input_tokens,
                        "avg_output_tokens": m.avg_output_tokens,
                        "total_cost_usd": m.total_cost_usd,
                        "avg_cost_per_execution": m.avg_cost_per_execution,
                    }
                    for m in models
                ]
                formatted = json.dumps(json_data, indent=2)
            else:
                # Table format (default)
                formatted = self._format_table(models, period, category)

            # Create reasoning for THINKING mode
            total_executions = sum(m.total_executions for m in models)
            period_desc = {
                "7d": "7 days",
                "30d": "30 days",
                "90d": "90 days",
                "all": "all time",
            }.get(period, period)
            category_desc = f" in category '{category}'" if category else ""
            reasoning = f"Analyzed {total_executions} execution(s) across {len(models)} model(s) from the last {period_desc}{category_desc}, calculating success rates, latency metrics, token usage, and cost data from the analytics database"

            return ExecutionResult(
                success=True,
                message=f"Model performance statistics for last {period}{category_desc}",
                data={
                    "models": [
                        {
                            "model": m.model,
                            "provider": m.provider,
                            "total_executions": m.total_executions,
                            "success_rate": m.success_rate,
                            "avg_ttft_ms": m.avg_ttft_ms,
                            "avg_execution_time_ms": m.avg_execution_time_ms,
                            "total_cost_usd": m.total_cost_usd,
                        }
                        for m in models
                    ],
                    "period": period,
                    "category": category,
                    "clean_output": formatted,
                    "reasoning": reasoning,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Error analyzing model performance: {str(e)}",
                data={"error": str(e), "clean_output": f"Error: {str(e)}"},
            )

    def _format_table(
        self, models: list, period: str, category: str | None
    ) -> str:
        """Format model statistics as a table.

        Args:
            models: List of ModelPerformanceMetrics
            period: Time period
            category: Optional category filter

        Returns:
            Formatted table string
        """
        output = []

        # Header
        period_desc = {
            "7d": "Last 7 Days",
            "30d": "Last 30 Days",
            "90d": "Last 90 Days",
            "all": "All Time",
        }.get(period, period)
        category_desc = f" - {category.replace('_', ' ').title()}" if category else ""
        output.append(f"📊 Model Performance Statistics ({period_desc}{category_desc})\n")

        # Summary
        total_executions = sum(m.total_executions for m in models)
        total_cost = sum(m.total_cost_usd for m in models)
        output.append(f"Total Executions: {total_executions:,}")
        output.append(f"Total Cost: ${total_cost:.4f}")
        output.append("")

        # Table header
        output.append(
            "┌─────────────────────┬────────────┬───────────┬────────────┬────────────┬──────────────┐"
        )
        output.append(
            "│ Model               │ Provider   │ Exec.     │ Success    │ Avg Time   │ Total Cost   │"
        )
        output.append(
            "├─────────────────────┼────────────┼───────────┼────────────┼────────────┼──────────────┤"
        )

        # Model rows
        for m in models:
            model_name = m.model[:19] if len(m.model) > 19 else m.model
            provider_name = (
                m.provider[:10] if m.provider and len(m.provider) > 10 else m.provider
            ) or "unknown"

            # Success rate (just percentage, no bars for better alignment)
            success_str = f"{m.success_rate:5.1f}%"

            # Format execution time (handle None case)
            if m.avg_execution_time_ms is None:
                time_str = "N/A"
            elif m.avg_execution_time_ms < 1000:
                time_str = f"{m.avg_execution_time_ms:.0f}ms"
            else:
                time_str = f"{m.avg_execution_time_ms/1000:.1f}s"

            output.append(
                f"│ {model_name:<19} │ {provider_name:<10} │ "
                f"{m.total_executions:>6,}    │ {success_str:>10} │ "
                f"{time_str:>9}  │ ${m.total_cost_usd:>11.4f} │"
            )

        output.append(
            "└─────────────────────┴────────────┴───────────┴────────────┴────────────┴──────────────┘"
        )

        # Token usage summary (if available)
        total_input = sum(m.total_input_tokens for m in models)
        total_output = sum(m.total_output_tokens for m in models)

        if total_input > 0 or total_output > 0:
            output.append("")
            output.append("📊 Token Usage:")
            output.append(f"  Input:  {total_input:>12,} tokens")
            output.append(f"  Output: {total_output:>12,} tokens")
            output.append(f"  Total:  {total_input + total_output:>12,} tokens")

        # Cost efficiency (tokens per dollar)
        if total_cost > 0:
            tokens_per_dollar = (total_input + total_output) / total_cost
            output.append(f"  Efficiency: {tokens_per_dollar:>8,.0f} tokens/$")

        return "\n".join(output)

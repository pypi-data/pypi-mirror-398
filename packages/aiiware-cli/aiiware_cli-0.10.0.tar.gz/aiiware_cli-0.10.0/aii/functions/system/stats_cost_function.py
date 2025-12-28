# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Cost analytics function - Analyze spending and cost trends."""


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
from aii.data.analytics.cost_analyzer import CostAnalyzer


class StatsCostFunction(FunctionPlugin):
    """Show cost breakdown and spending trends across models, categories, and providers.

    IMPORTANT: This function reads cost_usd from the database.
    It NEVER recalculates cost from tokens. Cost is calculated once by
    CostCalculator in executor.py and stored in the database as the single source of truth.
    """

    @property
    def name(self) -> str:
        return "stats_cost"

    @property
    def description(self) -> str:
        return "Show cost breakdown and spending trends including model costs, category costs, provider comparison, usage trends, growth rates, and budget projections"

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
            "breakdown_by": ParameterSchema(
                name="breakdown_by",
                type="string",
                required=False,
                default="all",
                description="Breakdown dimension (model, category, provider, client, all)",
            ),
            "show_trends": ParameterSchema(
                name="show_trends",
                type="boolean",
                required=False,
                default=False,
                description="Show usage trends and growth rates",
            ),
            "show_top_spenders": ParameterSchema(
                name="show_top_spenders",
                type="boolean",
                required=False,
                default=True,
                description="Show top spending functions",
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
        """Execute cost analysis.

        Args:
            parameters: Period, breakdown dimension, trend/spender flags, format
            context: Execution context

        Returns:
            ExecutionResult with cost breakdown and trends
        """
        period = parameters.get("period", "30d")
        breakdown_by = parameters.get("breakdown_by", "all")
        show_trends = parameters.get("show_trends", False)
        show_top_spenders = parameters.get("show_top_spenders", True)
        output_format = parameters.get("format", "table")

        # Validate period
        valid_periods = ["7d", "30d", "90d", "all"]
        if period not in valid_periods:
            return ExecutionResult(
                success=False,
                message=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}",
                data={"error": f"Invalid period: {period}"},
            )

        # Validate breakdown_by
        valid_breakdowns = ["model", "category", "provider", "client", "all"]
        if breakdown_by not in valid_breakdowns:
            return ExecutionResult(
                success=False,
                message=f"Invalid breakdown_by '{breakdown_by}'. Must be one of: {', '.join(valid_breakdowns)}",
                data={"error": f"Invalid breakdown_by: {breakdown_by}"},
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
            analyzer = CostAnalyzer(db_path, cache_ttl_seconds=60)

            # Get cost breakdown
            breakdown = await analyzer.get_cost_breakdown(
                period=period, breakdown_by=breakdown_by, use_cache=True
            )

            # Get client breakdown if requested (v0.9.2)
            client_costs = None
            if breakdown_by in ["client", "all"]:
                client_costs = await analyzer.get_cost_by_client(
                    period=period, use_cache=True
                )

            # Get trends if requested
            trends = None
            if show_trends:
                trends = await analyzer.get_usage_trends(period=period, use_cache=True)

            # Get top spenders if requested
            top_spenders = None
            if show_top_spenders:
                top_spenders = await analyzer.get_top_spenders(
                    period=period, limit=5
                )

            # Check if there's any data
            if breakdown.total_cost_usd == 0:
                period_desc = {
                    "7d": "7 days",
                    "30d": "30 days",
                    "90d": "90 days",
                    "all": "all time",
                }.get(period, period)

                return ExecutionResult(
                    success=True,
                    message=f"No cost data available for last {period_desc}",
                    data={
                        "breakdown": None,
                        "trends": None,
                        "top_spenders": None,
                        "period": period,
                        "clean_output": f"No cost data available for last {period_desc}.",
                    },
                )

            # Format output
            if output_format == "json":
                # JSON format
                json_data = {
                    "total_cost_usd": breakdown.total_cost_usd,
                    "period_days": breakdown.period_days,
                    "avg_daily_cost": breakdown.avg_daily_cost,
                    "projected_monthly_cost": breakdown.projected_monthly_cost,
                    "by_model": [{"name": name, "cost": cost} for name, cost in breakdown.by_model],
                    "by_category": [{"name": name, "cost": cost} for name, cost in breakdown.by_category],
                    "by_provider": [{"name": name, "cost": cost} for name, cost in breakdown.by_provider],
                }

                # Add client breakdown (v0.9.2)
                if client_costs:
                    json_data["by_client"] = [
                        {"name": name, "cost": cost}
                        for name, cost in sorted(
                            client_costs.items(), key=lambda x: x[1], reverse=True
                        )
                    ]

                if trends:
                    json_data["trends"] = {
                        "execution_growth_rate": trends.execution_growth_rate,
                        "cost_growth_rate": trends.cost_growth_rate,
                        "daily_executions": [{"date": dp.date, "value": dp.value} for dp in trends.daily_executions],
                        "daily_cost": [{"date": dp.date, "value": dp.value} for dp in trends.daily_cost],
                    }

                if top_spenders:
                    json_data["top_spenders"] = [
                        {"function": func, "model": model, "cost": cost}
                        for func, model, cost in top_spenders
                    ]

                formatted = json.dumps(json_data, indent=2)
            else:
                # Table format (default)
                formatted = self._format_table(
                    breakdown, trends, top_spenders, period, breakdown_by, client_costs
                )

            # Create reasoning for THINKING mode
            period_desc = {
                "7d": "7 days",
                "30d": "30 days",
                "90d": "90 days",
                "all": "all time",
            }.get(period, period)
            breakdown_dims = []
            if breakdown_by in ["model", "all"]:
                breakdown_dims.append(f"{len(breakdown.by_model)} models")
            if breakdown_by in ["category", "all"]:
                breakdown_dims.append(f"{len(breakdown.by_category)} categories")
            if breakdown_by in ["provider", "all"]:
                breakdown_dims.append(f"{len(breakdown.by_provider)} providers")
            if breakdown_by in ["client", "all"] and client_costs:
                breakdown_dims.append(f"{len(client_costs)} clients")
            breakdown_desc = ", ".join(breakdown_dims)

            reasoning = f"Analyzed cost data from the last {period_desc}, aggregating spending across {breakdown_desc}, calculating daily averages and monthly projections, "
            if show_trends:
                reasoning += "computing usage trends and growth rates, "
            if show_top_spenders:
                reasoning += "identifying top spending functions, "
            reasoning += "from the analytics database"

            return ExecutionResult(
                success=True,
                message=f"Cost analysis for last {period}",
                data={
                    "breakdown": {
                        "total_cost_usd": breakdown.total_cost_usd,
                        "avg_daily_cost": breakdown.avg_daily_cost,
                        "projected_monthly_cost": breakdown.projected_monthly_cost,
                        "by_model": breakdown.by_model[:5],
                        "by_category": breakdown.by_category[:5],
                        "by_provider": breakdown.by_provider,
                    },
                    "trends": {
                        "execution_growth_rate": trends.execution_growth_rate if trends else None,
                        "cost_growth_rate": trends.cost_growth_rate if trends else None,
                    }
                    if trends
                    else None,
                    "top_spenders": top_spenders,
                    "period": period,
                    "clean_output": formatted,
                    "reasoning": reasoning,
                },
            )

        except Exception as e:
            return ExecutionResult(
                success=False,
                message=f"Error analyzing costs: {str(e)}",
                data={"error": str(e), "clean_output": f"Error: {str(e)}"},
            )

    def _format_table(
        self,
        breakdown: Any,
        trends: Any | None,
        top_spenders: list[tuple[str, str, float]] | None,
        period: str,
        breakdown_by: str,
        client_costs: dict[str, float] | None = None,
    ) -> str:
        """Format cost statistics as a table.

        Args:
            breakdown: CostBreakdown object
            trends: UsageTrends object or None
            top_spenders: List of (function, model, cost) tuples or None
            period: Time period
            breakdown_by: Breakdown dimension
            client_costs: Client cost breakdown dict (v0.9.2)

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
        output.append(f"💰 Cost Analysis ({period_desc})\n")

        # Summary
        output.append(f"Total Cost: ${breakdown.total_cost_usd:.4f}")
        output.append(
            f"Average Daily: ${breakdown.avg_daily_cost:.4f} ({breakdown.period_days} days)"
        )
        output.append(
            f"Projected Monthly: ${breakdown.projected_monthly_cost:.4f}"
        )

        # Trends (if available)
        if trends:
            output.append("")
            output.append("📈 Growth Trends (Last 7 Days vs Previous 7 Days):")
            if trends.execution_growth_rate is not None:
                growth_symbol = (
                    "↑" if trends.execution_growth_rate > 0 else "↓" if trends.execution_growth_rate < 0 else "→"
                )
                output.append(
                    f"  Executions: {growth_symbol} {abs(trends.execution_growth_rate):.1f}%"
                )
            if trends.cost_growth_rate is not None:
                growth_symbol = (
                    "↑" if trends.cost_growth_rate > 0 else "↓" if trends.cost_growth_rate < 0 else "→"
                )
                output.append(
                    f"  Cost: {growth_symbol} {abs(trends.cost_growth_rate):.1f}%"
                )

        output.append("")

        # Cost breakdowns
        if breakdown_by in ["model", "all"] and breakdown.by_model:
            output.append("📊 Cost by Model:")
            output.append(
                "┌──────────────────────────┬──────────────┬────────────┐"
            )
            output.append(
                "│ Model                    │ Cost         │ Share      │"
            )
            output.append(
                "├──────────────────────────┼──────────────┼────────────┤"
            )

            for name, cost in breakdown.by_model[:5]:
                percentage = (
                    cost / breakdown.total_cost_usd * 100
                    if breakdown.total_cost_usd > 0
                    else 0
                )
                # Right-align percentage in 10-char column
                share_str = f"{percentage:5.1f}%"

                model_name = name[:24] if len(name) > 24 else name
                output.append(
                    f"│ {model_name:<24} │ ${cost:>11.4f} │ {share_str:>10} │"
                )

            output.append(
                "└──────────────────────────┴──────────────┴────────────┘"
            )
            output.append("")

        if breakdown_by in ["category", "all"] and breakdown.by_category:
            output.append("📊 Cost by Category:")
            output.append(
                "┌──────────────────────────┬──────────────┬────────────┐"
            )
            output.append(
                "│ Category                 │ Cost         │ Share      │"
            )
            output.append(
                "├──────────────────────────┼──────────────┼────────────┤"
            )

            for name, cost in breakdown.by_category[:5]:
                percentage = (
                    cost / breakdown.total_cost_usd * 100
                    if breakdown.total_cost_usd > 0
                    else 0
                )
                share_str = f"{percentage:5.1f}%"

                # Format category name
                category_name = name.replace("_", " ").title()[:24]
                output.append(
                    f"│ {category_name:<24} │ ${cost:>11.4f} │ {share_str:>10} │"
                )

            output.append(
                "└──────────────────────────┴──────────────┴────────────┘"
            )
            output.append("")

        if breakdown_by in ["client", "all"] and client_costs:
            output.append("📊 Cost by Client:")
            output.append(
                "┌──────────────────────────┬──────────────┬────────────┐"
            )
            output.append(
                "│ Client                   │ Cost         │ Share      │"
            )
            output.append(
                "├──────────────────────────┼──────────────┼────────────┤"
            )

            # Sort by cost descending
            sorted_clients = sorted(
                client_costs.items(), key=lambda x: x[1], reverse=True
            )

            for name, cost in sorted_clients:
                percentage = (
                    cost / breakdown.total_cost_usd * 100
                    if breakdown.total_cost_usd > 0
                    else 0
                )
                share_str = f"{percentage:5.1f}%"

                # Format client name (cli, vscode, chrome, api)
                client_name = name.upper() if name == "cli" else name.capitalize()
                if name == "vscode":
                    client_name = "Aii VSCode"
                elif name == "chrome":
                    client_name = "Aii Chrome"
                elif name == "cli":
                    client_name = "Aii CLI"
                elif name == "api":
                    client_name = "Aii API"

                client_name = client_name[:24]
                output.append(
                    f"│ {client_name:<24} │ ${cost:>11.4f} │ {share_str:>10} │"
                )

            output.append(
                "└──────────────────────────┴──────────────┴────────────┘"
            )
            output.append("")

        if breakdown_by in ["provider", "all"] and breakdown.by_provider:
            output.append("📊 Cost by Provider:")
            output.append(
                "┌──────────────────────────┬──────────────┬────────────┐"
            )
            output.append(
                "│ Provider                 │ Cost         │ Share      │"
            )
            output.append(
                "├──────────────────────────┼──────────────┼────────────┤"
            )

            for name, cost in breakdown.by_provider:
                percentage = (
                    cost / breakdown.total_cost_usd * 100
                    if breakdown.total_cost_usd > 0
                    else 0
                )
                share_str = f"{percentage:5.1f}%"

                provider_name = name.capitalize()[:24]
                output.append(
                    f"│ {provider_name:<24} │ ${cost:>11.4f} │ {share_str:>10} │"
                )

            output.append(
                "└──────────────────────────┴──────────────┴────────────┘"
            )
            output.append("")

        # Top spenders
        if top_spenders:
            output.append("🔥 Top Spending Functions:")
            output.append(
                "┌──────────────────────────┬──────────────────────┬──────────────┐"
            )
            output.append(
                "│ Function                 │ Model                │ Cost         │"
            )
            output.append(
                "├──────────────────────────┼──────────────────────┼──────────────┤"
            )

            for func, model, cost in top_spenders:
                func_name = func[:24] if len(func) > 24 else func
                model_name = model[:20] if len(model) > 20 else model
                output.append(
                    f"│ {func_name:<24} │ {model_name:<20} │ ${cost:>11.4f} │"
                )

            output.append(
                "└──────────────────────────┴──────────────────────┴──────────────┘"
            )

        return "\n".join(output)

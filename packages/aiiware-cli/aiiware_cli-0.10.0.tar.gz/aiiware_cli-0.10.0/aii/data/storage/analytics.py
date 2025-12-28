# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Analytics module for querying session/execution statistics."""


import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from pathlib import Path
import aiosqlite


class SessionAnalytics:
    """Query execution history for analytics and insights."""

    def __init__(self, db_path: Path | None = None):
        """Initialize analytics with database path.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.aii/chats.db
        """
        if db_path is None:
            db_path = Path.home() / ".aii" / "chats.db"

        self.db_path = db_path

    async def get_usage_stats(
        self,
        period: str,
        breakdown: str
    ) -> Dict[str, Any]:
        """Get aggregated usage statistics.

        Args:
            period: Time period ('7d', '30d', '90d', 'all')
            breakdown: Type of breakdown ('functions', 'tokens', 'cost', 'all')

        Returns:
            Dictionary with aggregated statistics
        """
        # Convert period to datetime
        since = self._parse_period(period)

        # Query executions since period
        executions = await self._get_executions_since(since)

        # Aggregate statistics based on breakdown
        stats = {
            "total_sessions": len(executions),
            "period": period,
            "date_range": {
                "start": since.isoformat() if since != datetime.min else "all time",
                "end": datetime.now().isoformat()
            }
        }

        if breakdown in ["functions", "all"]:
            stats["functions"] = self._aggregate_functions(executions)

        if breakdown in ["tokens", "all"]:
            stats["tokens"] = self._aggregate_tokens(executions)

        if breakdown in ["cost", "all"]:
            stats["costs"] = self._aggregate_costs(executions)

        return stats

    def _parse_period(self, period: str) -> datetime:
        """Convert period string to datetime.

        Args:
            period: Period string ('7d', '30d', '90d', 'all')

        Returns:
            Datetime for start of period
        """
        now = datetime.now()

        if period == "7d":
            return now - timedelta(days=7)
        elif period == "30d":
            return now - timedelta(days=30)
        elif period == "90d":
            return now - timedelta(days=90)
        elif period == "all":
            return datetime.min  # Beginning of time
        else:
            raise ValueError(f"Invalid period: {period}")

    async def _get_executions_since(self, since: datetime) -> List[Dict[str, Any]]:
        """Get all executions since a given datetime.

        Args:
            since: Start datetime for filtering

        Returns:
            List of execution dictionaries
        """
        executions = []

        try:
            async with aiosqlite.connect(str(self.db_path)) as db:
                db.row_factory = aiosqlite.Row

                query = """
                    SELECT function_name, parameters, result, timestamp, success
                    FROM executions
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """

                async with db.execute(query, (since.isoformat(),)) as cursor:
                    rows = await cursor.fetchall()

                    for row in rows:
                        execution = {
                            "function_name": row["function_name"],
                            "parameters": json.loads(row["parameters"] or "{}"),
                            "result": json.loads(row["result"] or "{}"),
                            "timestamp": datetime.fromisoformat(row["timestamp"]),
                            "success": bool(row["success"])
                        }
                        executions.append(execution)

        except Exception as e:
            # If database doesn't exist or table doesn't exist, return empty list
            # This handles the case where aii is brand new
            pass

        return executions

    def _aggregate_functions(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate function usage counts.

        Args:
            executions: List of execution dictionaries

        Returns:
            Dictionary with function aggregation stats
        """
        function_counts = {}

        for execution in executions:
            func_name = execution.get("function_name")
            if func_name:
                if func_name not in function_counts:
                    function_counts[func_name] = 0
                function_counts[func_name] += 1

        # Sort by usage (descending)
        sorted_functions = sorted(
            function_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "by_function": sorted_functions[:10],  # Top 10
            "total_functions_used": len(function_counts),
            "total_executions": sum(function_counts.values())
        }

    def _aggregate_tokens(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate token usage.

        Extracts token information from execution results.

        Args:
            executions: List of execution dictionaries

        Returns:
            Dictionary with token aggregation stats
        """
        total_input = 0
        total_output = 0
        by_function = {}

        for execution in executions:
            # Try to extract token usage from result
            result = execution.get("result", {})

            # Token usage might be in different places depending on function
            # Common patterns: result.tokens, result.token_usage, result.data.tokens
            tokens = {}

            if isinstance(result, dict):
                tokens = result.get("tokens", result.get("token_usage", {}))

                # Also check in data field
                if not tokens and "data" in result:
                    data = result["data"]
                    if isinstance(data, dict):
                        tokens = data.get("tokens", data.get("token_usage", {}))

            input_tokens = 0
            output_tokens = 0

            if isinstance(tokens, dict):
                input_tokens = tokens.get("input_tokens", tokens.get("input", 0))
                output_tokens = tokens.get("output_tokens", tokens.get("output", 0))

            total_input += input_tokens
            total_output += output_tokens

            # Aggregate by function
            func_name = execution.get("function_name")
            if func_name and (input_tokens > 0 or output_tokens > 0):
                if func_name not in by_function:
                    by_function[func_name] = {"input": 0, "output": 0}

                by_function[func_name]["input"] += input_tokens
                by_function[func_name]["output"] += output_tokens

        # Sort by total tokens
        sorted_by_tokens = sorted(
            by_function.items(),
            key=lambda x: x[1]["input"] + x[1]["output"],
            reverse=True
        )

        return {
            "total_input": total_input,
            "total_output": total_output,
            "total_tokens": total_input + total_output,
            "by_function": dict(sorted_by_tokens[:10])  # Top 10
        }

    def _aggregate_costs(self, executions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate cost by function.

        Uses actual costs from execution results when available,
        falls back to estimation for older data.

        Args:
            executions: List of execution dictionaries

        Returns:
            Dictionary with cost aggregation stats
        """
        # Fallback pricing (for older executions without cost data)
        # Claude Sonnet: $3/1M input, $15/1M output
        COST_PER_1K_INPUT = 0.003
        COST_PER_1K_OUTPUT = 0.015

        total_cost = 0.0
        by_function = {}

        for execution in executions:
            result = execution.get("result", {})
            cost = 0.0

            if isinstance(result, dict):
                # Try to get actual cost from execution result
                cost = result.get("cost", 0.0)

                # Check nested data field as fallback
                if cost == 0.0 and "data" in result:
                    data = result["data"]
                    if isinstance(data, dict):
                        cost = data.get("cost", 0.0)

                # If no cost found, try to estimate from tokens (backward compatibility)
                if cost == 0.0:
                    # Try to extract tokens
                    tokens = result.get("tokens", result.get("token_usage", {}))

                    if not tokens and "data" in result:
                        data = result["data"]
                        if isinstance(data, dict):
                            tokens = data.get("tokens", data.get("token_usage", {}))

                    if isinstance(tokens, dict):
                        input_tokens = tokens.get("input_tokens", tokens.get("input", 0))
                        output_tokens = tokens.get("output_tokens", tokens.get("output", 0))

                        # Estimate cost using fallback pricing
                        cost = (input_tokens / 1000.0 * COST_PER_1K_INPUT +
                               output_tokens / 1000.0 * COST_PER_1K_OUTPUT)

            if cost > 0:
                total_cost += cost

                # Aggregate by function
                func_name = execution.get("function_name")
                if func_name:
                    if func_name not in by_function:
                        by_function[func_name] = 0.0
                    by_function[func_name] += cost

        # Sort by cost
        sorted_costs = sorted(
            by_function.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return {
            "total_cost": total_cost,
            "by_function": sorted_costs[:10]  # Top 10 by cost
        }

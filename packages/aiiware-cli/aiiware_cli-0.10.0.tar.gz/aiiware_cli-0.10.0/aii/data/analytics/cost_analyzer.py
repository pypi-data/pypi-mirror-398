# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Cost Analyzer - Analyze spending and cost trends"""


import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiosqlite

from .models import CostBreakdown, TimeSeriesDataPoint, UsageTrends


class CostAnalyzer:
    """
    Analyze cost metrics and spending patterns.

    Features:
    - Total cost by time period
    - Cost breakdown (model, category, provider)
    - Daily/weekly/monthly aggregations
    - Cost projections based on trends
    - Growth rate calculations
    - Query result caching (1-minute TTL)
    """

    def __init__(self, db_path: Path, cache_ttl_seconds: int = 60):
        """
        Initialize cost analyzer.

        Args:
            db_path: Path to SQLite database
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self.db_path = db_path
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict = {}
        self._cache_timestamps: dict = {}

    def _get_cache_key(self, method: str, **kwargs) -> str:
        """Generate cache key from method name and parameters"""
        params = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return f"{method}:{params}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        age = time.time() - self._cache_timestamps[cache_key]
        return age < self.cache_ttl_seconds

    def _get_cached(self, cache_key: str):
        """Get cached result if valid"""
        if self._is_cache_valid(cache_key):
            return self._cache.get(cache_key)
        return None

    def _set_cache(self, cache_key: str, value):
        """Cache a result"""
        self._cache[cache_key] = value
        self._cache_timestamps[cache_key] = time.time()

    def _get_date_filter(self, period: str) -> Optional[str]:
        """Get date filter SQL for time period"""
        if period == "all":
            return None

        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 30)

        cutoff_date = datetime.now() - timedelta(days=days)
        return cutoff_date.isoformat()

    def _get_period_days(self, period: str) -> int:
        """Get number of days in period"""
        days_map = {"7d": 7, "30d": 30, "90d": 90, "all": 365}
        return days_map.get(period, 30)

    async def get_cost_breakdown(
        self,
        period: str = "30d",
        breakdown_by: str = "model",
        use_cache: bool = True,
    ) -> CostBreakdown:
        """
        Get cost breakdown by model, category, or provider.

        Args:
            period: "7d", "30d", "90d", or "all"
            breakdown_by: "model", "category", or "provider"
            use_cache: Whether to use cached results

        Returns:
            CostBreakdown with total cost and breakdowns
        """
        # Check cache
        cache_key = self._get_cache_key(
            "get_cost_breakdown", period=period, breakdown_by=breakdown_by
        )
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        date_filter = self._get_date_filter(period)
        period_days = self._get_period_days(period)

        # Query total cost
        total_query = "SELECT SUM(cost_usd) as total_cost FROM executions WHERE 1=1"
        params = []

        if date_filter:
            total_query += " AND timestamp >= ?"
            params.append(date_filter)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row

            # Get total cost
            async with db.execute(total_query, params) as cursor:
                row = await cursor.fetchone()
                total_cost = row["total_cost"] or 0.0

            # Get breakdown by model
            by_model = await self._get_breakdown_by_field(
                db, "model", date_filter, params
            )

            # Get breakdown by category
            by_category = await self._get_breakdown_by_field(
                db, "function_category", date_filter, params
            )

            # Get breakdown by provider
            by_provider = await self._get_breakdown_by_field(
                db, "provider", date_filter, params
            )

            # Calculate projections
            avg_daily_cost = 0.0
            if period_days > 0:
                # Get actual number of days with data
                days_query = """
                    SELECT COUNT(DISTINCT DATE(timestamp)) as days_with_data
                    FROM executions
                    WHERE 1=1
                """
                days_params = []
                if date_filter:
                    days_query += " AND timestamp >= ?"
                    days_params.append(date_filter)

                async with db.execute(days_query, days_params) as cursor:
                    row = await cursor.fetchone()
                    days_with_data = row["days_with_data"] or 1

                avg_daily_cost = total_cost / days_with_data if days_with_data > 0 else 0.0

            projected_monthly_cost = avg_daily_cost * 30

        breakdown = CostBreakdown(
            total_cost_usd=round(total_cost, 4),
            period_days=period_days,
            by_model=by_model,
            by_category=by_category,
            by_provider=by_provider,
            avg_daily_cost=round(avg_daily_cost, 4),
            projected_monthly_cost=round(projected_monthly_cost, 4),
        )

        # Cache result
        self._set_cache(cache_key, breakdown)

        return breakdown

    async def get_cost_by_client(
        self,
        period: str = "30d",
        use_cache: bool = True,
    ) -> dict[str, float]:
        """
        Get cost breakdown by client type (cli, vscode, chrome, api).

        Args:
            period: "7d", "30d", "90d", or "all"
            use_cache: Whether to use cached results

        Returns:
            Dictionary mapping client_type to total cost
        """
        # Check cache
        cache_key = self._get_cache_key("get_cost_by_client", period=period)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        date_filter = self._get_date_filter(period)

        query = """
            SELECT client_type, SUM(cost_usd) as total_cost
            FROM executions
            WHERE client_type IS NOT NULL
        """
        params = []

        if date_filter:
            query += " AND timestamp >= ?"
            params.append(date_filter)

        query += " GROUP BY client_type ORDER BY total_cost DESC"

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

        # Build result dictionary
        result = {row["client_type"]: round(row["total_cost"], 4) for row in rows}

        # Cache result
        self._set_cache(cache_key, result)

        return result

    async def _get_breakdown_by_field(
        self,
        db: aiosqlite.Connection,
        field: str,
        date_filter: Optional[str],
        base_params: list,
    ) -> list[tuple[str, float]]:
        """Get cost breakdown by a specific field"""
        query = f"""
            SELECT {field}, SUM(cost_usd) as total_cost
            FROM executions
            WHERE {field} IS NOT NULL
        """

        params = []
        if date_filter:
            query += " AND timestamp >= ?"
            params.append(date_filter)

        query += f"""
            GROUP BY {field}
            ORDER BY total_cost DESC
        """

        breakdown = []
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                name = row[field] or "unknown"
                cost = round(row["total_cost"], 4)
                breakdown.append((name, cost))

        return breakdown

    async def get_usage_trends(
        self,
        period: str = "30d",
        use_cache: bool = True,
    ) -> UsageTrends:
        """
        Get usage trends over time.

        Args:
            period: "7d", "30d", "90d", or "all"
            use_cache: Whether to use cached results

        Returns:
            UsageTrends with time series data
        """
        # Check cache
        cache_key = self._get_cache_key("get_usage_trends", period=period)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        date_filter = self._get_date_filter(period)

        query = """
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as execution_count,
                SUM(cost_usd) as daily_cost,
                SUM(input_tokens + output_tokens) as daily_tokens
            FROM executions
            WHERE 1=1
        """

        params = []
        if date_filter:
            query += " AND timestamp >= ?"
            params.append(date_filter)

        query += """
            GROUP BY DATE(timestamp)
            ORDER BY date ASC
        """

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

                daily_executions = []
                daily_cost = []
                daily_tokens = []

                for row in rows:
                    date = row["date"]
                    daily_executions.append(
                        TimeSeriesDataPoint(
                            date=date, value=float(row["execution_count"])
                        )
                    )
                    daily_cost.append(
                        TimeSeriesDataPoint(
                            date=date, value=round(row["daily_cost"], 4)
                        )
                    )
                    daily_tokens.append(
                        TimeSeriesDataPoint(
                            date=date, value=float(row["daily_tokens"])
                        )
                    )

        # Calculate growth rates (compare last 7 days to previous 7 days)
        execution_growth = None
        cost_growth = None

        if len(daily_executions) >= 14:
            # Last 7 days
            recent_executions = sum(
                dp.value for dp in daily_executions[-7:]
            )
            previous_executions = sum(
                dp.value for dp in daily_executions[-14:-7]
            )

            if previous_executions > 0:
                execution_growth = (
                    (recent_executions - previous_executions) / previous_executions * 100
                )

            # Cost growth
            recent_cost = sum(dp.value for dp in daily_cost[-7:])
            previous_cost = sum(dp.value for dp in daily_cost[-14:-7])

            if previous_cost > 0:
                cost_growth = (
                    (recent_cost - previous_cost) / previous_cost * 100
                )

        trends = UsageTrends(
            daily_executions=daily_executions,
            daily_cost=daily_cost,
            daily_tokens=daily_tokens,
            execution_growth_rate=(
                round(execution_growth, 2) if execution_growth is not None else None
            ),
            cost_growth_rate=(
                round(cost_growth, 2) if cost_growth is not None else None
            ),
        )

        # Cache result
        self._set_cache(cache_key, trends)

        return trends

    async def get_top_spenders(
        self,
        period: str = "30d",
        limit: int = 10,
    ) -> list[tuple[str, str, float]]:
        """
        Get top spending functions or models.

        Args:
            period: "7d", "30d", "90d", or "all"
            limit: Number of results to return

        Returns:
            List of (function_name, model, cost) tuples
        """
        date_filter = self._get_date_filter(period)

        query = """
            SELECT
                function_name,
                model,
                SUM(cost_usd) as total_cost
            FROM executions
            WHERE 1=1
        """

        params = []
        if date_filter:
            query += " AND timestamp >= ?"
            params.append(date_filter)

        query += """
            GROUP BY function_name, model
            ORDER BY total_cost DESC
            LIMIT ?
        """
        params.append(limit)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    (
                        row["function_name"],
                        row["model"] or "unknown",
                        round(row["total_cost"], 4),
                    )
                    for row in rows
                ]

    def clear_cache(self):
        """Clear all cached results"""
        self._cache.clear()
        self._cache_timestamps.clear()

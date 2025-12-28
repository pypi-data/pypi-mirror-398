# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Model Performance Analyzer - Analyze model execution metrics"""


import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiosqlite

from .models import ModelPerformanceMetrics, FunctionPerformanceMetrics


class ModelPerformanceAnalyzer:
    """
    Analyze model performance metrics from execution logs.

    Features:
    - Success rates by model
    - Average latency (TTFT, total time)
    - Token usage statistics
    - Cost analysis
    - Time period filtering
    - Category filtering
    - Query result caching (1-minute TTL)
    """

    def __init__(self, db_path: Path, cache_ttl_seconds: int = 60):
        """
        Initialize analyzer.

        Args:
            db_path: Path to SQLite database
            cache_ttl_seconds: Cache time-to-live in seconds (default: 60)
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
        """
        Get date filter SQL for time period.

        Args:
            period: "7d", "30d", "90d", or "all"

        Returns:
            ISO format date string or None for "all"
        """
        if period == "all":
            return None

        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period, 30)

        cutoff_date = datetime.now() - timedelta(days=days)
        return cutoff_date.isoformat()

    async def get_model_performance(
        self,
        period: str = "30d",
        category: Optional[str] = None,
        use_cache: bool = True,
    ) -> list[ModelPerformanceMetrics]:
        """
        Get performance metrics for all models.

        Args:
            period: "7d", "30d", "90d", or "all"
            category: Optional function category filter
            use_cache: Whether to use cached results

        Returns:
            List of ModelPerformanceMetrics sorted by total executions
        """
        # Check cache
        cache_key = self._get_cache_key(
            "get_model_performance", period=period, category=category
        )
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        # Build query
        date_filter = self._get_date_filter(period)

        query = """
            SELECT
                model,
                provider,
                COUNT(*) as total_executions,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_executions,
                AVG(time_to_first_token_ms) as avg_ttft_ms,
                AVG(total_execution_time_ms) as avg_execution_time_ms,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                AVG(input_tokens) as avg_input_tokens,
                AVG(output_tokens) as avg_output_tokens,
                SUM(cost_usd) as total_cost_usd,
                AVG(cost_usd) as avg_cost_per_execution
            FROM executions
            WHERE model IS NOT NULL
        """

        params = []

        if date_filter:
            query += " AND timestamp >= ?"
            params.append(date_filter)

        if category:
            query += " AND function_category = ?"
            params.append(category)

        query += """
            GROUP BY model, provider
            ORDER BY total_executions DESC
        """

        # Execute query
        results = []
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

                for row in rows:
                    total = row["total_executions"]
                    success = row["successful_executions"]
                    success_rate = (success / total * 100) if total > 0 else 0.0

                    metrics = ModelPerformanceMetrics(
                        model=row["model"],
                        provider=row["provider"],
                        total_executions=total,
                        successful_executions=success,
                        failed_executions=row["failed_executions"],
                        success_rate=round(success_rate, 2),
                        avg_ttft_ms=(
                            round(row["avg_ttft_ms"], 1)
                            if row["avg_ttft_ms"]
                            else None
                        ),
                        avg_execution_time_ms=(
                            round(row["avg_execution_time_ms"], 1)
                            if row["avg_execution_time_ms"]
                            else None
                        ),
                        total_input_tokens=row["total_input_tokens"] or 0,
                        total_output_tokens=row["total_output_tokens"] or 0,
                        avg_input_tokens=(
                            round(row["avg_input_tokens"], 1)
                            if row["avg_input_tokens"]
                            else None
                        ),
                        avg_output_tokens=(
                            round(row["avg_output_tokens"], 1)
                            if row["avg_output_tokens"]
                            else None
                        ),
                        total_cost_usd=(
                            round(row["total_cost_usd"], 4)
                            if row["total_cost_usd"]
                            else 0.0
                        ),
                        avg_cost_per_execution=(
                            round(row["avg_cost_per_execution"], 6)
                            if row["avg_cost_per_execution"]
                            else None
                        ),
                    )
                    results.append(metrics)

        # Cache results
        self._set_cache(cache_key, results)

        return results

    async def get_function_performance(
        self,
        period: str = "30d",
        use_cache: bool = True,
    ) -> list[FunctionPerformanceMetrics]:
        """
        Get performance metrics for all functions.

        Args:
            period: "7d", "30d", "90d", or "all"
            use_cache: Whether to use cached results

        Returns:
            List of FunctionPerformanceMetrics sorted by total executions
        """
        # Check cache
        cache_key = self._get_cache_key("get_function_performance", period=period)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        date_filter = self._get_date_filter(period)

        # Main query for function stats
        query = """
            SELECT
                function_name,
                function_category,
                COUNT(*) as total_executions,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_executions,
                AVG(total_execution_time_ms) as avg_execution_time_ms,
                SUM(cost_usd) as total_cost_usd
            FROM executions
            WHERE 1=1
        """

        params = []
        if date_filter:
            query += " AND timestamp >= ?"
            params.append(date_filter)

        query += """
            GROUP BY function_name, function_category
            ORDER BY total_executions DESC
        """

        results = []
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()

                for row in rows:
                    function_name = row["function_name"]

                    # Get top models for this function
                    top_models_query = """
                        SELECT model, COUNT(*) as count
                        FROM executions
                        WHERE function_name = ?
                    """
                    top_params = [function_name]

                    if date_filter:
                        top_models_query += " AND timestamp >= ?"
                        top_params.append(date_filter)

                    top_models_query += """
                        GROUP BY model
                        ORDER BY count DESC
                        LIMIT 3
                    """

                    top_models = []
                    async with db.execute(
                        top_models_query, top_params
                    ) as models_cursor:
                        model_rows = await models_cursor.fetchall()
                        top_models = [
                            (r["model"], r["count"]) for r in model_rows if r["model"]
                        ]

                    total = row["total_executions"]
                    success = row["successful_executions"]
                    success_rate = (success / total * 100) if total > 0 else 0.0

                    metrics = FunctionPerformanceMetrics(
                        function_name=function_name,
                        function_category=row["function_category"],
                        total_executions=total,
                        successful_executions=success,
                        failed_executions=row["failed_executions"],
                        success_rate=round(success_rate, 2),
                        top_models=top_models,
                        avg_execution_time_ms=(
                            round(row["avg_execution_time_ms"], 1)
                            if row["avg_execution_time_ms"]
                            else None
                        ),
                        total_cost_usd=(
                            round(row["total_cost_usd"], 4)
                            if row["total_cost_usd"]
                            else 0.0
                        ),
                    )
                    results.append(metrics)

        # Cache results
        self._set_cache(cache_key, results)

        return results

    async def get_model_comparison(
        self, models: list[str], period: str = "30d"
    ) -> dict[str, ModelPerformanceMetrics]:
        """
        Compare performance metrics for specific models.

        Args:
            models: List of model names to compare
            period: "7d", "30d", "90d", or "all"

        Returns:
            Dict mapping model name to metrics
        """
        all_metrics = await self.get_model_performance(period=period, use_cache=True)

        comparison = {}
        for metrics in all_metrics:
            if metrics.model in models:
                comparison[metrics.model] = metrics

        return comparison

    def clear_cache(self):
        """Clear all cached results"""
        self._cache.clear()
        self._cache_timestamps.clear()

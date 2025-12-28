# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Analytics data models"""


from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a single model"""

    model: str
    provider: Optional[str]
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float  # Percentage (0-100)

    # Latency metrics (milliseconds)
    avg_ttft_ms: Optional[float]  # Time To First Token
    avg_execution_time_ms: float

    # Token usage
    total_input_tokens: int
    total_output_tokens: int
    avg_input_tokens: float
    avg_output_tokens: float

    # Cost
    total_cost_usd: float
    avg_cost_per_execution: float


@dataclass
class FunctionPerformanceMetrics:
    """Performance metrics for a single function"""

    function_name: str
    function_category: Optional[str]
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float

    # Most used models for this function
    top_models: list[tuple[str, int]]  # [(model, count), ...]

    avg_execution_time_ms: float
    total_cost_usd: float


@dataclass
class CostBreakdown:
    """Cost breakdown by various dimensions"""

    total_cost_usd: float
    period_days: int

    # Breakdown by model
    by_model: list[tuple[str, float]]  # [(model, cost), ...]

    # Breakdown by function category
    by_category: list[tuple[str, float]]  # [(category, cost), ...]

    # Breakdown by provider
    by_provider: list[tuple[str, float]]  # [(provider, cost), ...]

    # Projections
    avg_daily_cost: float
    projected_monthly_cost: float


@dataclass
class TimeSeriesDataPoint:
    """Single data point for time series"""

    date: str  # ISO format date
    value: float
    label: Optional[str] = None


@dataclass
class UsageTrends:
    """Usage trends over time"""

    # Daily execution counts
    daily_executions: list[TimeSeriesDataPoint]

    # Daily cost
    daily_cost: list[TimeSeriesDataPoint]

    # Daily token usage
    daily_tokens: list[TimeSeriesDataPoint]

    # Growth rate (percentage change)
    execution_growth_rate: Optional[float]  # 7-day over previous 7-day
    cost_growth_rate: Optional[float]

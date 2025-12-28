# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Statistics and analytics endpoints (v0.9.0)."""


from fastapi import APIRouter, HTTPException, Depends, Query
from pathlib import Path
from typing import Optional

from aii.api.models import (
    ModelStatsResponse,
    CostStatsResponse,
)
from aii.api.middleware import verify_api_key, check_rate_limit, get_server_instance
from aii.data.analytics.model_performance_analyzer import ModelPerformanceAnalyzer
from aii.data.analytics.cost_analyzer import CostAnalyzer

router = APIRouter()


@router.get("/api/stats/models", response_model=ModelStatsResponse)
async def get_model_stats(
    period: str = Query("30d", description="Time period (7d, 30d, 90d, all)"),
    category: Optional[str] = Query(None, description="Filter by function category"),
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
):
    """
    Get model performance statistics.

    Returns success rates, latency metrics, token usage, and cost analysis
    for all LLM models used during the specified time period.

    **Parameters**:
    - `period`: Time period for statistics (7d, 30d, 90d, all). Default: 30d
    - `category`: Optional function category filter (translation, analysis, etc.)

    **Response**:
    ```json
    {
      "models": [
        {
          "model": "gpt-4o",
          "provider": "openai",
          "total_executions": 102,
          "successful_executions": 100,
          "failed_executions": 2,
          "success_rate": 98.0,
          "avg_ttft_ms": 300,
          "avg_execution_time_ms": 987,
          "total_input_tokens": 5600,
          "total_output_tokens": 12300,
          "avg_input_tokens": 55,
          "avg_output_tokens": 121,
          "total_cost_usd": 0.0252,
          "avg_cost_per_execution": 0.000247
        }
      ],
      "period": "30d",
      "category": null,
      "total_executions": 234,
      "total_cost": 0.1234
    }
    ```

    **Authentication**: Requires valid API key in `Aii-API-Key` header.

    **Rate Limit**: 100 requests per hour per API key.
    """
    server = get_server_instance()

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Validate period
    valid_periods = ["7d", "30d", "90d", "all"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}",
        )

    try:
        # Get database path
        db_path = Path.home() / ".aii" / "chats.db"

        if not db_path.exists():
            raise HTTPException(
                status_code=404, detail="No analytics data available. Database not found."
            )

        # Create analyzer
        analyzer = ModelPerformanceAnalyzer(db_path, cache_ttl_seconds=60)

        # Get model performance data
        models = await analyzer.get_model_performance(
            period=period, category=category, use_cache=True
        )

        # Calculate totals
        total_executions = sum(m.total_executions for m in models)
        total_cost = sum(m.total_cost_usd for m in models)

        # Build response
        return ModelStatsResponse(
            models=[
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
            ],
            period=period,
            category=category,
            total_executions=total_executions,
            total_cost=total_cost,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing model performance: {str(e)}"
        )


@router.get("/api/stats/cost", response_model=CostStatsResponse)
async def get_cost_stats(
    period: str = Query("30d", description="Time period (7d, 30d, 90d, all)"),
    breakdown_by: str = Query(
        "all", description="Breakdown dimension (model, category, provider, all)"
    ),
    show_trends: bool = Query(False, description="Include usage trends and growth rates"),
    show_top_spenders: bool = Query(True, description="Include top spending functions"),
    top_limit: int = Query(5, description="Number of top spenders to return (1-20)"),
    api_key: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
):
    """
    Get cost breakdown and spending trends.

    Returns comprehensive cost analysis including breakdowns by model/category/provider,
    usage trends with growth rates, monthly projections, and top spending functions.

    **Parameters**:
    - `period`: Time period for statistics (7d, 30d, 90d, all). Default: 30d
    - `breakdown_by`: Breakdown dimension (model, category, provider, all). Default: all
    - `show_trends`: Include usage trends and growth rates. Default: false
    - `show_top_spenders`: Include top spending functions. Default: true
    - `top_limit`: Number of top spenders to return (1-20). Default: 5

    **Response**:
    ```json
    {
      "breakdown": {
        "total_cost_usd": 0.1234,
        "period_days": 30,
        "avg_daily_cost": 0.0041,
        "projected_monthly_cost": 0.1230,
        "by_model": [["gpt-4o", 0.0389], ["claude-3.5-sonnet", 0.0451]],
        "by_category": [["translation", 0.0389], ["analysis", 0.0451]],
        "by_provider": [["openai", 0.0783], ["anthropic", 0.0451]]
      },
      "trends": {
        "execution_growth_rate": 15.5,
        "cost_growth_rate": 20.3,
        "daily_executions": [...],
        "daily_cost": [...],
        "daily_tokens": [...]
      },
      "top_spenders": [
        {"function": "explain", "model": "claude-3.5-sonnet", "cost": 0.0451}
      ],
      "period": "30d"
    }
    ```

    **Authentication**: Requires valid API key in `Aii-API-Key` header.

    **Rate Limit**: 100 requests per hour per API key.
    """
    server = get_server_instance()

    if not server:
        raise HTTPException(status_code=500, detail="Server not initialized")

    # Validate period
    valid_periods = ["7d", "30d", "90d", "all"]
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period '{period}'. Must be one of: {', '.join(valid_periods)}",
        )

    # Validate breakdown_by
    valid_breakdowns = ["model", "category", "provider", "all"]
    if breakdown_by not in valid_breakdowns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid breakdown_by '{breakdown_by}'. Must be one of: {', '.join(valid_breakdowns)}",
        )

    # Validate top_limit
    if top_limit < 1 or top_limit > 20:
        raise HTTPException(
            status_code=400, detail="top_limit must be between 1 and 20"
        )

    try:
        # Get database path
        db_path = Path.home() / ".aii" / "chats.db"

        if not db_path.exists():
            raise HTTPException(
                status_code=404, detail="No analytics data available. Database not found."
            )

        # Create analyzer
        analyzer = CostAnalyzer(db_path, cache_ttl_seconds=60)

        # Get cost breakdown
        breakdown = await analyzer.get_cost_breakdown(
            period=period, breakdown_by=breakdown_by, use_cache=True
        )

        # Get trends if requested
        trends = None
        if show_trends:
            trends_data = await analyzer.get_usage_trends(period=period, use_cache=True)
            trends = {
                "execution_growth_rate": trends_data.execution_growth_rate,
                "cost_growth_rate": trends_data.cost_growth_rate,
                "daily_executions": [
                    {"date": dp.date, "value": dp.value}
                    for dp in trends_data.daily_executions
                ],
                "daily_cost": [
                    {"date": dp.date, "value": dp.value} for dp in trends_data.daily_cost
                ],
                "daily_tokens": [
                    {"date": dp.date, "value": dp.value}
                    for dp in trends_data.daily_tokens
                ],
            }

        # Get top spenders if requested
        top_spenders = None
        if show_top_spenders:
            spenders = await analyzer.get_top_spenders(period=period, limit=top_limit)
            top_spenders = [
                {"function": func, "model": model, "cost": cost}
                for func, model, cost in spenders
            ]

        # Build response
        return CostStatsResponse(
            breakdown={
                "total_cost_usd": breakdown.total_cost_usd,
                "period_days": breakdown.period_days,
                "avg_daily_cost": breakdown.avg_daily_cost,
                "projected_monthly_cost": breakdown.projected_monthly_cost,
                "by_model": breakdown.by_model,
                "by_category": breakdown.by_category,
                "by_provider": breakdown.by_provider,
            },
            trends=trends,
            top_spenders=top_spenders,
            period=period,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error analyzing costs: {str(e)}"
        )

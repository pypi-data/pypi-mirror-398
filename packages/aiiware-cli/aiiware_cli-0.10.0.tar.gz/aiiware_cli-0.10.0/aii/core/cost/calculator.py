# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Cost Calculator - Track LLM usage costs and budget management"""


import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

# Import pricing data
from .pricing import get_model_pricing, calculate_cost as pricing_calculate_cost, format_cost


class CostProvider(Enum):
    """Supported LLM providers for cost calculation"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    GEMINI = "gemini"


@dataclass
class ModelPricing:
    """Pricing information for a specific model"""
    provider: CostProvider
    model_name: str
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    reasoning_cost_per_1k: float = 0.0  # Cost per 1K reasoning tokens (for o1 models)
    currency: str = "USD"


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a single operation"""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    reasoning_cost: float = 0.0
    total_cost: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Calculate total cost after initialization"""
        self.total_cost = self.input_cost + self.output_cost + self.reasoning_cost


@dataclass
class BudgetAlert:
    """Budget alert configuration"""
    threshold_percentage: float  # 0.0 to 1.0
    message: str
    alert_level: str  # "info", "warning", "critical"


class CostCalculator:
    """Calculate costs for LLM usage across different providers"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / ".aii"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.cost_history_file = self.storage_path / "cost_history.json"

        # Current pricing (updated as of January 2025)
        self.pricing_models = {
            # Anthropic Claude Models
            CostProvider.ANTHROPIC: {
                "claude-3-5-sonnet-20241022": ModelPricing(
                    provider=CostProvider.ANTHROPIC,
                    model_name="claude-3-5-sonnet-20241022",
                    input_cost_per_1k=3.00,   # $3.00 per 1M tokens
                    output_cost_per_1k=15.00   # $15.00 per 1M tokens
                ),
                "claude-3-5-haiku-20241022": ModelPricing(
                    provider=CostProvider.ANTHROPIC,
                    model_name="claude-3-5-haiku-20241022",
                    input_cost_per_1k=1.00,   # $1.00 per 1M tokens
                    output_cost_per_1k=5.00    # $5.00 per 1M tokens
                ),
                "claude-3-opus-20240229": ModelPricing(
                    provider=CostProvider.ANTHROPIC,
                    model_name="claude-3-opus-20240229",
                    input_cost_per_1k=15.00,  # $15.00 per 1M tokens
                    output_cost_per_1k=75.00   # $75.00 per 1M tokens
                ),
            },
            # OpenAI Models
            CostProvider.OPENAI: {
                "gpt-4o": ModelPricing(
                    provider=CostProvider.OPENAI,
                    model_name="gpt-4o",
                    input_cost_per_1k=5.00,   # $5.00 per 1M tokens
                    output_cost_per_1k=15.00   # $15.00 per 1M tokens
                ),
                "gpt-4o-mini": ModelPricing(
                    provider=CostProvider.OPENAI,
                    model_name="gpt-4o-mini",
                    input_cost_per_1k=0.15,   # $0.15 per 1M tokens
                    output_cost_per_1k=0.60    # $0.60 per 1M tokens
                ),
                "o1-preview": ModelPricing(
                    provider=CostProvider.OPENAI,
                    model_name="o1-preview",
                    input_cost_per_1k=15.00,  # $15.00 per 1M tokens
                    output_cost_per_1k=60.00,  # $60.00 per 1M tokens
                    reasoning_cost_per_1k=60.00  # $60.00 per 1M reasoning tokens
                ),
                "o1-mini": ModelPricing(
                    provider=CostProvider.OPENAI,
                    model_name="o1-mini",
                    input_cost_per_1k=3.00,   # $3.00 per 1M tokens
                    output_cost_per_1k=12.00,  # $12.00 per 1M tokens
                    reasoning_cost_per_1k=12.00  # $12.00 per 1M reasoning tokens
                ),
            },
            # Google Gemini Models
            CostProvider.GOOGLE: {
                "gemini-1.5-pro": ModelPricing(
                    provider=CostProvider.GOOGLE,
                    model_name="gemini-1.5-pro",
                    input_cost_per_1k=7.00,   # $7.00 per 1M tokens
                    output_cost_per_1k=21.00   # $21.00 per 1M tokens
                ),
                "gemini-1.5-flash": ModelPricing(
                    provider=CostProvider.GOOGLE,
                    model_name="gemini-1.5-flash",
                    input_cost_per_1k=0.075,  # $0.075 per 1M tokens
                    output_cost_per_1k=0.30    # $0.30 per 1M tokens
                ),
            }
        }

        # Default budget alerts
        self.default_budget_alerts = [
            BudgetAlert(0.75, "Budget 75% used - consider monitoring usage", "warning"),
            BudgetAlert(0.90, "Budget 90% used - approaching limit", "critical"),
            BudgetAlert(1.0, "Budget exceeded - usage beyond daily limit", "critical")
        ]

        # Load existing cost history
        self.cost_history = self._load_cost_history()

    def calculate_cost(self, provider: str, model: str, input_tokens: int,
                      output_tokens: int, reasoning_tokens: int = 0) -> CostBreakdown:
        """
        Calculate cost for a specific LLM operation using latest pricing data.

        Args:
            provider: Provider name (anthropic, openai, gemini)
            model: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            reasoning_tokens: Number of reasoning tokens (for extended thinking)

        Returns:
            CostBreakdown with detailed cost information
        """
        # Try to use new pricing module first
        total_cost = pricing_calculate_cost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_write_tokens=0,  # TODO: Add cache token tracking
            cache_read_tokens=0
        )

        if total_cost is not None:
            # Successfully calculated with new pricing
            # Get pricing details for breakdown
            pricing_info = get_model_pricing(provider, model)

            input_cost = (input_tokens / 1_000_000) * pricing_info.input_price if pricing_info else 0.0
            output_cost = (output_tokens / 1_000_000) * pricing_info.output_price if pricing_info else 0.0
            reasoning_cost = 0.0  # TODO: Add reasoning token pricing

            breakdown = CostBreakdown(
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                reasoning_tokens=reasoning_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                reasoning_cost=reasoning_cost
            )
        else:
            # Fallback to legacy pricing (for unknown models)
            provider_enum = self._normalize_provider(provider)
            pricing = self._find_pricing_model(provider_enum, model)

            if not pricing:
                # Return zero cost if pricing not found
                breakdown = CostBreakdown(
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    reasoning_tokens=reasoning_tokens,
                    input_cost=0.0,
                    output_cost=0.0,
                    reasoning_cost=0.0
                )
            else:
                # Use legacy pricing calculation
                input_cost = (input_tokens / 1000) * (pricing.input_cost_per_1k / 1000)
                output_cost = (output_tokens / 1000) * (pricing.output_cost_per_1k / 1000)
                reasoning_cost = (reasoning_tokens / 1000) * (pricing.reasoning_cost_per_1k / 1000)

                breakdown = CostBreakdown(
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    reasoning_tokens=reasoning_tokens,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    reasoning_cost=reasoning_cost
                )

        # Store in cost history
        self._add_to_history(breakdown)

        return breakdown

    def get_daily_spending(self, date: Optional[datetime] = None) -> float:
        """Get total spending for a specific date (default: today)"""
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        daily_costs = []

        for entry in self.cost_history:
            entry_date = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d")
            if entry_date == date_str:
                daily_costs.append(entry["total_cost"])

        return sum(daily_costs)

    def get_weekly_spending(self) -> float:
        """Get total spending for the past 7 days"""
        one_week_ago = datetime.now() - timedelta(days=7)
        weekly_costs = []

        for entry in self.cost_history:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if entry_date >= one_week_ago:
                weekly_costs.append(entry["total_cost"])

        return sum(weekly_costs)

    def get_monthly_spending(self) -> float:
        """Get total spending for the current month"""
        current_month = datetime.now().strftime("%Y-%m")
        monthly_costs = []

        for entry in self.cost_history:
            entry_month = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m")
            if entry_month == current_month:
                monthly_costs.append(entry["total_cost"])

        return sum(monthly_costs)

    def check_budget_alerts(self, daily_budget: float) -> List[BudgetAlert]:
        """Check if any budget alerts should be triggered"""
        daily_spending = self.get_daily_spending()
        triggered_alerts = []

        if daily_budget <= 0:
            return triggered_alerts

        usage_percentage = daily_spending / daily_budget

        for alert in self.default_budget_alerts:
            if usage_percentage >= alert.threshold_percentage:
                triggered_alerts.append(alert)

        return triggered_alerts

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary"""
        daily_spending = self.get_daily_spending()
        weekly_spending = self.get_weekly_spending()
        monthly_spending = self.get_monthly_spending()

        # Provider breakdown for today
        today_providers = {}
        date_str = datetime.now().strftime("%Y-%m-%d")

        for entry in self.cost_history:
            entry_date = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d")
            if entry_date == date_str:
                provider = entry["provider"]
                if provider not in today_providers:
                    today_providers[provider] = {
                        "cost": 0.0,
                        "tokens": 0,
                        "calls": 0
                    }
                today_providers[provider]["cost"] += entry["total_cost"]
                today_providers[provider]["tokens"] += (
                    entry["input_tokens"] + entry["output_tokens"] + entry["reasoning_tokens"]
                )
                today_providers[provider]["calls"] += 1

        return {
            "daily_spending": daily_spending,
            "weekly_spending": weekly_spending,
            "monthly_spending": monthly_spending,
            "provider_breakdown": today_providers,
            "total_operations": len([
                e for e in self.cost_history
                if datetime.fromisoformat(e["timestamp"]).strftime("%Y-%m-%d") == date_str
            ])
        }

    def format_cost(self, amount: float) -> str:
        """Format cost amount for display"""
        if amount == 0.0:
            return "$0.00"
        elif amount < 0.001:
            return f"${amount:.6f}"
        elif amount < 0.01:
            return f"${amount:.4f}"
        else:
            return f"${amount:.2f}"

    def _normalize_provider(self, provider: str) -> CostProvider:
        """Normalize provider string to enum"""
        provider_lower = provider.lower()
        if "anthropic" in provider_lower or "claude" in provider_lower:
            return CostProvider.ANTHROPIC
        elif "openai" in provider_lower or "gpt" in provider_lower:
            return CostProvider.OPENAI
        elif "google" in provider_lower or "gemini" in provider_lower:
            return CostProvider.GOOGLE
        else:
            # Default to Anthropic if unknown
            return CostProvider.ANTHROPIC

    def _find_pricing_model(self, provider: CostProvider, model: str) -> Optional[ModelPricing]:
        """Find pricing information for a specific model"""
        if provider not in self.pricing_models:
            return None

        provider_models = self.pricing_models[provider]

        # Try exact match first
        if model in provider_models:
            return provider_models[model]

        # Try fuzzy matching for common variations
        model_lower = model.lower()
        for model_key, pricing in provider_models.items():
            if model_lower in model_key.lower() or model_key.lower() in model_lower:
                return pricing

        # No match found
        return None

    def _add_to_history(self, breakdown: CostBreakdown) -> None:
        """Add cost breakdown to history"""
        entry = {
            "timestamp": breakdown.timestamp.isoformat(),
            "provider": breakdown.provider,
            "model": breakdown.model,
            "input_tokens": breakdown.input_tokens,
            "output_tokens": breakdown.output_tokens,
            "reasoning_tokens": breakdown.reasoning_tokens,
            "input_cost": breakdown.input_cost,
            "output_cost": breakdown.output_cost,
            "reasoning_cost": breakdown.reasoning_cost,
            "total_cost": breakdown.total_cost
        }

        self.cost_history.append(entry)

        # Save to file
        self._save_cost_history()

    def _load_cost_history(self) -> List[Dict[str, Any]]:
        """Load cost history from file"""
        if not self.cost_history_file.exists():
            return []

        try:
            with open(self.cost_history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_cost_history(self) -> None:
        """Save cost history to file"""
        try:
            # Keep only last 1000 entries to prevent file from growing too large
            if len(self.cost_history) > 1000:
                self.cost_history = self.cost_history[-1000:]

            with open(self.cost_history_file, 'w') as f:
                json.dump(self.cost_history, f, indent=2)
        except IOError:
            pass  # Silently ignore file write errors

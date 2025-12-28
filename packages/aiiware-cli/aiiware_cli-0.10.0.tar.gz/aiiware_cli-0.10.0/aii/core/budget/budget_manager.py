# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Budget Manager - Single Responsibility: Budget Monitoring and Alerts

Extracted from AIIEngine to follow SRP (Single Responsibility Principle).
This class is responsible ONLY for:
- Checking budget status
- Generating budget warnings
- Determining if operations are within budget
"""


from typing import List

from ..cost.calculator import CostCalculator
from ...config.output_config import OutputConfig


class BudgetManager:
    """
    Manages budget monitoring and alerts.

    Following SOLID principles:
    - SRP: Only responsible for budget-related operations
    - DIP: Depends on abstractions (CostCalculator, OutputConfig)
    - ISP: Minimal interface with only budget-related methods
    """

    def __init__(self, cost_calculator: CostCalculator, output_config: OutputConfig):
        """
        Initialize budget manager.

        Args:
            cost_calculator: Calculator for tracking costs
            output_config: Output configuration with budget settings
        """
        self.cost_calculator = cost_calculator
        self.output_config = output_config

    def check_warnings(self) -> List[str]:
        """
        Check budget status and return any warnings.

        Returns:
            List of warning messages (empty if no warnings)
        """
        warnings = []

        if not self.output_config.show_budget_warnings or self.output_config.daily_budget <= 0:
            return warnings

        try:
            # Get current spending
            daily_spending = self.cost_calculator.get_daily_spending()
            usage_percentage = daily_spending / self.output_config.daily_budget

            # Check against thresholds (highest to lowest)
            sorted_thresholds = sorted(self.output_config.budget_alert_thresholds, reverse=True)

            for threshold in sorted_thresholds:
                if usage_percentage >= threshold:
                    if threshold >= 1.0:
                        warnings.append(
                            f"⚠️ Budget exceeded: ${daily_spending:.4f} / ${self.output_config.daily_budget:.2f} ({usage_percentage*100:.0f}%)"
                        )
                    elif threshold >= 0.90:
                        warnings.append(
                            f"⚠️ Budget 90% used: ${daily_spending:.4f} / ${self.output_config.daily_budget:.2f}"
                        )
                    elif threshold >= 0.75:
                        warnings.append(
                            f"💰 Budget 75% used: ${daily_spending:.4f} / ${self.output_config.daily_budget:.2f}"
                        )
                    break  # Only show the highest applicable warning

        except Exception:
            # Silently ignore budget check errors
            pass

        return warnings

    def is_within_budget(self) -> bool:
        """
        Check if current spending is within budget.

        Returns:
            True if within budget, False otherwise
        """
        if self.output_config.daily_budget <= 0:
            return True  # No budget limit set

        try:
            daily_spending = self.cost_calculator.get_daily_spending()
            return daily_spending < self.output_config.daily_budget
        except Exception:
            return True  # Assume within budget if check fails

    def get_spending_summary(self) -> dict:
        """
        Get current spending summary.

        Returns:
            Dictionary with spending details:
            - daily_spending: Current daily spending
            - daily_budget: Daily budget limit
            - usage_percentage: Percentage of budget used
            - remaining: Remaining budget
        """
        try:
            daily_spending = self.cost_calculator.get_daily_spending()
            daily_budget = self.output_config.daily_budget

            if daily_budget > 0:
                usage_percentage = (daily_spending / daily_budget) * 100
                remaining = max(0, daily_budget - daily_spending)
            else:
                usage_percentage = 0
                remaining = 0

            return {
                "daily_spending": daily_spending,
                "daily_budget": daily_budget,
                "usage_percentage": usage_percentage,
                "remaining": remaining,
                "within_budget": self.is_within_budget()
            }
        except Exception:
            return {
                "daily_spending": 0,
                "daily_budget": self.output_config.daily_budget,
                "usage_percentage": 0,
                "remaining": self.output_config.daily_budget,
                "within_budget": True
            }

    def display_warnings(self) -> None:
        """Display budget warnings to console."""
        warnings = self.check_warnings()
        for warning in warnings:
            print(warning)

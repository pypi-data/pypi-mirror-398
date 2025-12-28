# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Health check system for aii diagnostics"""


import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional


class HealthStatus(Enum):
    """Health check result status"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class HealthCheckResult:
    """Result from a health check"""
    name: str
    status: HealthStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    fix_suggestion: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        """Check if status indicates health"""
        return self.status in [HealthStatus.PASSED, HealthStatus.SKIPPED]

    @property
    def icon(self) -> str:
        """Get emoji icon for status"""
        return {
            HealthStatus.PASSED: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.FAILED: "❌",
            HealthStatus.SKIPPED: "⏭️",
        }[self.status]


class HealthCheck(ABC):
    """Base class for health checks"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """
        Perform the health check

        Args:
            context: Dictionary with system context (config, providers, etc.)

        Returns:
            HealthCheckResult with status and details
        """
        pass

    def _create_result(
        self,
        status: HealthStatus,
        message: str,
        details: dict[str, Any] | None = None,
        fix_suggestion: str | None = None,
    ) -> HealthCheckResult:
        """Helper to create a result"""
        return HealthCheckResult(
            name=self.name,
            status=status,
            message=message,
            details=details or {},
            fix_suggestion=fix_suggestion,
        )


class ConfigHealthCheck(HealthCheck):
    """Check configuration file validity"""

    def __init__(self):
        super().__init__(
            name="Configuration",
            description="Verify config file exists and is valid"
        )

    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """Check config file"""
        config_manager = context.get("config_manager")

        if not config_manager:
            return self._create_result(
                HealthStatus.FAILED,
                "Config manager not available",
                fix_suggestion="Restart the application"
            )

        config_path = config_manager.config_file

        if not config_path.exists():
            return self._create_result(
                HealthStatus.FAILED,
                f"Config file not found: {config_path}",
                details={"path": str(config_path)},
                fix_suggestion=f"Run: aii config init"
            )

        try:
            # Try to read config
            config = config_manager.get_all_config()

            return self._create_result(
                HealthStatus.PASSED,
                f"Config file valid: {config_path}",
                details={
                    "path": str(config_path),
                    "llm_provider": config.get("llm.provider", "not set"),
                    "llm_model": config.get("llm.model", "not set"),
                }
            )
        except Exception as e:
            return self._create_result(
                HealthStatus.FAILED,
                f"Config file invalid: {str(e)}",
                details={"error": str(e)},
                fix_suggestion="Run: aii config validate"
            )


class LLMProviderHealthCheck(HealthCheck):
    """Check LLM provider connectivity"""

    def __init__(self):
        super().__init__(
            name="LLM Provider",
            description="Verify LLM provider is configured and accessible"
        )

    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """Check LLM provider"""
        llm_provider = context.get("llm_provider")
        config_manager = context.get("config_manager")

        if not llm_provider:
            llm_provider_name = config_manager.get("llm.provider") if config_manager else "unknown"
            return self._create_result(
                HealthStatus.FAILED,
                f"LLM provider not initialized: {llm_provider_name}",
                fix_suggestion="Check API key configuration"
            )

        # Test with a simple prompt
        try:
            response = await llm_provider.complete("Hello", max_tokens=10)

            return self._create_result(
                HealthStatus.PASSED,
                f"LLM provider connected: {llm_provider.provider_name}",
                details={
                    "provider": llm_provider.provider_name,
                    "model": llm_provider.model,
                    "test_response_length": len(response),
                }
            )
        except Exception as e:
            error_str = str(e).lower()

            if "api key" in error_str or "unauthorized" in error_str:
                fix_suggestion = f"Set API key: export {llm_provider.provider_name.upper()}_API_KEY=your-key"
            elif "rate limit" in error_str:
                fix_suggestion = "Wait a moment and try again (rate limited)"
            else:
                fix_suggestion = "Check network connection and API key"

            return self._create_result(
                HealthStatus.FAILED,
                f"LLM provider error: {str(e)[:100]}",
                details={"error": str(e)},
                fix_suggestion=fix_suggestion
            )


class WebSearchHealthCheck(HealthCheck):
    """Check web search provider"""

    def __init__(self):
        super().__init__(
            name="Web Search",
            description="Verify web search provider is configured"
        )

    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """Check web search"""
        web_client = context.get("web_client")
        config_manager = context.get("config_manager")

        if not web_client:
            return self._create_result(
                HealthStatus.WARNING,
                "Web search not configured (optional)",
                fix_suggestion="Configure Brave API key for web search"
            )

        # Test search
        try:
            results = await web_client.search("test", num_results=1)

            return self._create_result(
                HealthStatus.PASSED,
                f"Web search working ({len(results)} result)",
                details={"provider": "web_search", "results": len(results)}
            )
        except Exception as e:
            return self._create_result(
                HealthStatus.WARNING,
                f"Web search error: {str(e)[:100]}",
                details={"error": str(e)},
                fix_suggestion="Check web search API key or network"
            )


class StorageHealthCheck(HealthCheck):
    """Check storage/database health"""

    def __init__(self):
        super().__init__(
            name="Storage",
            description="Verify database is writable and accessible"
        )

    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """Check storage"""
        storage_path = context.get("storage_path")

        if not storage_path:
            # v0.6.0: Storage lives on server side, skip check for local CLI
            return self._create_result(
                HealthStatus.SKIPPED,
                "Storage managed by server (use 'aii serve status' to check server health)"
            )

        storage_path = Path(storage_path)

        # Check directory exists and is writable
        try:
            storage_path.mkdir(parents=True, exist_ok=True)

            # Try to create a test file
            test_file = storage_path / ".health_check_test"
            test_file.write_text("test")
            test_file.unlink()

            # Check database file
            db_file = storage_path / "conversations.db"
            db_exists = db_file.exists()
            db_size = db_file.stat().st_size if db_exists else 0

            return self._create_result(
                HealthStatus.PASSED,
                f"Storage accessible: {storage_path}",
                details={
                    "path": str(storage_path),
                    "writable": True,
                    "db_exists": db_exists,
                    "db_size_mb": round(db_size / (1024 * 1024), 2) if db_exists else 0,
                }
            )
        except PermissionError:
            return self._create_result(
                HealthStatus.FAILED,
                f"Storage not writable: {storage_path}",
                details={"path": str(storage_path)},
                fix_suggestion=f"Check permissions: chmod 755 {storage_path}"
            )
        except Exception as e:
            return self._create_result(
                HealthStatus.FAILED,
                f"Storage error: {str(e)}",
                details={"error": str(e)},
                fix_suggestion="Check disk space and permissions"
            )


class FunctionRegistryHealthCheck(HealthCheck):
    """Check function registry status"""

    def __init__(self):
        super().__init__(
            name="Function Registry",
            description="Verify all functions are loaded"
        )

    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """Check function registry"""
        function_registry = context.get("function_registry")

        if not function_registry:
            # v0.6.0: Function registry lives on server side, skip check for local CLI
            return self._create_result(
                HealthStatus.SKIPPED,
                "Functions managed by server (use 'aii serve status' to check server health)"
            )

        try:
            functions = function_registry.list_functions()
            function_count = len(functions)

            if function_count == 0:
                return self._create_result(
                    HealthStatus.FAILED,
                    "No functions registered",
                    fix_suggestion="Check function loading at startup"
                )

            # Expected minimum function count (adjust as needed)
            expected_min = 20

            if function_count < expected_min:
                return self._create_result(
                    HealthStatus.WARNING,
                    f"Only {function_count} functions loaded (expected ≥{expected_min})",
                    details={
                        "loaded": function_count,
                        "expected_min": expected_min,
                        "functions": [f.name for f in functions],
                    },
                    fix_suggestion="Some functions may have failed to load"
                )

            return self._create_result(
                HealthStatus.PASSED,
                f"{function_count} functions loaded",
                details={
                    "count": function_count,
                    "functions": [f.name for f in functions],
                }
            )
        except Exception as e:
            return self._create_result(
                HealthStatus.FAILED,
                f"Function registry error: {str(e)}",
                details={"error": str(e)}
            )


class BudgetHealthCheck(HealthCheck):
    """Check budget status"""

    def __init__(self):
        super().__init__(
            name="Budget",
            description="Check daily spending against budget"
        )

    async def check(self, context: dict[str, Any]) -> HealthCheckResult:
        """Check budget"""
        cost_calculator = context.get("cost_calculator")
        output_config = context.get("output_config")

        if not cost_calculator:
            return self._create_result(
                HealthStatus.SKIPPED,
                "Budget tracking not available"
            )

        if not output_config or output_config.daily_budget <= 0:
            return self._create_result(
                HealthStatus.SKIPPED,
                "Budget not configured"
            )

        try:
            daily_spending = cost_calculator.get_daily_spending()
            daily_budget = output_config.daily_budget
            usage_percentage = (daily_spending / daily_budget) * 100

            if usage_percentage >= 100:
                return self._create_result(
                    HealthStatus.FAILED,
                    f"Budget exceeded: ${daily_spending:.2f} / ${daily_budget:.2f}",
                    details={
                        "spent": daily_spending,
                        "budget": daily_budget,
                        "percentage": round(usage_percentage, 1),
                    },
                    fix_suggestion="Increase budget or wait for daily reset"
                )
            elif usage_percentage >= 80:
                return self._create_result(
                    HealthStatus.WARNING,
                    f"Budget at {usage_percentage:.0f}%: ${daily_spending:.2f} / ${daily_budget:.2f}",
                    details={
                        "spent": daily_spending,
                        "budget": daily_budget,
                        "percentage": round(usage_percentage, 1),
                    },
                    fix_suggestion="Consider increasing budget"
                )
            else:
                return self._create_result(
                    HealthStatus.PASSED,
                    f"Budget healthy: ${daily_spending:.2f} / ${daily_budget:.2f} ({usage_percentage:.0f}%)",
                    details={
                        "spent": daily_spending,
                        "budget": daily_budget,
                        "percentage": round(usage_percentage, 1),
                    }
                )
        except Exception as e:
            return self._create_result(
                HealthStatus.WARNING,
                f"Budget check error: {str(e)}",
                details={"error": str(e)}
            )


class HealthCheckRunner:
    """Runs health checks and formats results"""

    def __init__(self, use_colors: bool = True, use_emojis: bool = True):
        self.use_colors = use_colors
        self.use_emojis = use_emojis
        self.checks: List[HealthCheck] = []

    def register_check(self, check: HealthCheck):
        """Register a health check"""
        self.checks.append(check)

    def register_default_checks(self):
        """Register all default health checks"""
        self.checks = [
            ConfigHealthCheck(),
            LLMProviderHealthCheck(),
            WebSearchHealthCheck(),
            StorageHealthCheck(),
            FunctionRegistryHealthCheck(),
            BudgetHealthCheck(),
        ]

    async def run_all(self, context: dict[str, Any]) -> List[HealthCheckResult]:
        """Run all registered health checks"""
        results = []

        for check in self.checks:
            try:
                result = await check.check(context)
                results.append(result)
            except Exception as e:
                # If check itself crashes, create a failed result
                results.append(
                    HealthCheckResult(
                        name=check.name,
                        status=HealthStatus.FAILED,
                        message=f"Health check crashed: {str(e)}",
                        details={"error": str(e)},
                    )
                )

        return results

    def format_results(self, results: List[HealthCheckResult]) -> str:
        """Format health check results for display"""
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("🏥 AII Health Check Results" if self.use_emojis else "AII Health Check Results")
        lines.append("=" * 70)
        lines.append("")

        # Summary counts
        passed = sum(1 for r in results if r.status == HealthStatus.PASSED)
        warnings = sum(1 for r in results if r.status == HealthStatus.WARNING)
        failed = sum(1 for r in results if r.status == HealthStatus.FAILED)
        skipped = sum(1 for r in results if r.status == HealthStatus.SKIPPED)

        lines.append(f"Total Checks: {len(results)}")
        lines.append(f"  ✅ Passed: {passed}" if self.use_emojis else f"  Passed: {passed}")
        if warnings > 0:
            lines.append(f"  ⚠️  Warnings: {warnings}" if self.use_emojis else f"  Warnings: {warnings}")
        if failed > 0:
            lines.append(f"  ❌ Failed: {failed}" if self.use_emojis else f"  Failed: {failed}")
        if skipped > 0:
            lines.append(f"  ⏭️  Skipped: {skipped}" if self.use_emojis else f"  Skipped: {skipped}")
        lines.append("")
        lines.append("-" * 70)
        lines.append("")

        # Individual results
        for result in results:
            icon = result.icon if self.use_emojis else f"[{result.status.value}]"
            lines.append(f"{icon} {result.name}")
            lines.append(f"   {result.message}")

            if result.fix_suggestion:
                lines.append(f"   💡 Fix: {result.fix_suggestion}" if self.use_emojis else f"   Fix: {result.fix_suggestion}")

            if result.details:
                for key, value in result.details.items():
                    if key != "error":  # Don't duplicate error message
                        lines.append(f"      • {key}: {value}")

            lines.append("")

        # Footer
        lines.append("-" * 70)

        # Overall status
        if failed > 0:
            overall = "❌ System has issues that need attention" if self.use_emojis else "System has issues"
        elif warnings > 0:
            overall = "⚠️  System is functional but has warnings" if self.use_emojis else "System has warnings"
        else:
            overall = "✅ All systems operational" if self.use_emojis else "All systems operational"

        lines.append(overall)
        lines.append("=" * 70)

        return "\n".join(lines)

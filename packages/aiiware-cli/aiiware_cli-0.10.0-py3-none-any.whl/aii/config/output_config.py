# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""Output Configuration System for Enhanced Session Management"""


import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from ..cli.footer_formatter import VerbosityLevel


class OutputFormat(Enum):
    """Output format options"""
    STANDARD = "standard"
    JSON = "json"
    MINIMAL = "minimal"
    DETAILED = "detailed"


@dataclass
class OutputConfig:
    """Comprehensive output configuration with multiple sources"""

    # Core verbosity settings
    verbosity: VerbosityLevel = VerbosityLevel.STANDARD
    output_format: OutputFormat = OutputFormat.STANDARD

    # Display options
    show_llm_provider: bool = True
    show_timing: bool = True
    show_tokens: bool = True
    show_confidence: bool = False
    show_session_info: bool = False
    show_cost_estimates: bool = False
    show_function_pipeline: bool = False
    show_artifacts: bool = True
    show_performance_metrics: bool = False

    # Semantic analysis options
    enable_semantic_analysis: bool = True
    semantic_analysis_verbosity_threshold: VerbosityLevel = VerbosityLevel.STANDARD

    # Visual options
    use_colors: bool = True
    use_emojis: bool = True
    use_animations: bool = True

    # Advanced options
    enable_debug_mode: bool = False
    enable_trace_mode: bool = False
    max_session_history: int = 100
    auto_save_sessions: bool = True

    # Budget management
    daily_budget: float = 5.0  # Default $5 daily budget
    show_budget_warnings: bool = True
    budget_alert_thresholds: List[float] = field(default_factory=lambda: [0.75, 0.90, 1.0])  # 75%, 90%, 100%

    # Output customization
    custom_footer_fields: Dict[str, bool] = field(default_factory=dict)
    custom_header_fields: Dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_cli_args(cls, args: Any) -> 'OutputConfig':
        """Create configuration from CLI arguments"""
        config = cls()

        # Handle verbosity flags
        if hasattr(args, 'minimal') and args.minimal:
            config.verbosity = VerbosityLevel.MINIMAL
            config.show_timing = False
            config.show_tokens = False
            config.show_confidence = False
            config.enable_semantic_analysis = False

        elif hasattr(args, 'verbose') and args.verbose:
            config.verbosity = VerbosityLevel.DETAILED
            config.show_confidence = True
            config.show_session_info = True
            config.show_cost_estimates = True
            config.show_function_pipeline = True
            config.show_performance_metrics = True

        elif hasattr(args, 'debug') and args.debug:
            config.verbosity = VerbosityLevel.DETAILED
            config.enable_debug_mode = True
            config.enable_trace_mode = True
            config.show_confidence = True
            config.show_session_info = True
            config.show_cost_estimates = True
            config.show_function_pipeline = True
            config.show_performance_metrics = True

        # Handle specific display flags
        if hasattr(args, 'no_colors') and args.no_colors:
            config.use_colors = False

        if hasattr(args, 'no_emojis') and args.no_emojis:
            config.use_emojis = False

        if hasattr(args, 'no_animations') and args.no_animations:
            config.use_animations = False

        if hasattr(args, 'show_tokens') and args.show_tokens:
            config.show_tokens = True

        if hasattr(args, 'show_confidence') and args.show_confidence:
            config.show_confidence = True

        if hasattr(args, 'show_cost') and args.show_cost:
            config.show_cost_estimates = True

        return config

    @classmethod
    def from_config_file(cls, path: Optional[str] = None) -> 'OutputConfig':
        """Load configuration from file"""
        if path is None:
            # Try default locations
            config_paths = [
                Path.home() / ".aii" / "output.json",
                Path.cwd() / ".aii-output.json"
            ]

            for config_path in config_paths:
                if config_path.exists():
                    path = str(config_path)
                    break
            else:
                # No config file found, return defaults
                return cls()

        try:
            with open(path, 'r') as f:
                data = json.load(f)

            config = cls()

            # Map JSON keys to dataclass fields
            if 'verbosity' in data:
                config.verbosity = VerbosityLevel(data['verbosity'])
            if 'output_format' in data:
                config.output_format = OutputFormat(data['output_format'])

            # Boolean display options
            bool_fields = [
                'show_llm_provider', 'show_timing', 'show_tokens', 'show_confidence',
                'show_session_info', 'show_cost_estimates', 'show_function_pipeline',
                'show_artifacts', 'show_performance_metrics', 'enable_semantic_analysis',
                'use_colors', 'use_emojis', 'use_animations', 'enable_debug_mode',
                'enable_trace_mode', 'auto_save_sessions'
            ]

            for field_name in bool_fields:
                if field_name in data:
                    setattr(config, field_name, bool(data[field_name]))

            # Integer fields
            if 'max_session_history' in data:
                config.max_session_history = int(data['max_session_history'])

            # Custom field configurations
            if 'custom_footer_fields' in data:
                config.custom_footer_fields = data['custom_footer_fields']
            if 'custom_header_fields' in data:
                config.custom_header_fields = data['custom_header_fields']

            return config

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not load config file {path}: {e}")
            return cls()

    @classmethod
    def from_environment(cls) -> 'OutputConfig':
        """Load configuration from environment variables"""
        config = cls()

        # Verbosity level
        if 'AII_VERBOSITY' in os.environ:
            try:
                verbosity_map = {
                    'minimal': VerbosityLevel.MINIMAL,
                    'standard': VerbosityLevel.STANDARD,
                    'detailed': VerbosityLevel.DETAILED,
                    'verbose': VerbosityLevel.DETAILED,
                    'debug': VerbosityLevel.DETAILED
                }
                config.verbosity = verbosity_map.get(
                    os.environ['AII_VERBOSITY'].lower(),
                    VerbosityLevel.STANDARD
                )
            except (KeyError, ValueError):
                pass

        # Output format
        if 'AII_OUTPUT_FORMAT' in os.environ:
            try:
                config.output_format = OutputFormat(os.environ['AII_OUTPUT_FORMAT'].lower())
            except ValueError:
                pass

        # Boolean environment variables
        bool_env_map = {
            'AII_SHOW_LLM_PROVIDER': 'show_llm_provider',
            'AII_SHOW_TIMING': 'show_timing',
            'AII_SHOW_TOKENS': 'show_tokens',
            'AII_SHOW_CONFIDENCE': 'show_confidence',
            'AII_SHOW_SESSION_INFO': 'show_session_info',
            'AII_SHOW_COST': 'show_cost_estimates',
            'AII_SHOW_PIPELINE': 'show_function_pipeline',
            'AII_SHOW_ARTIFACTS': 'show_artifacts',
            'AII_SHOW_PERFORMANCE': 'show_performance_metrics',
            'AII_ENABLE_SEMANTIC_ANALYSIS': 'enable_semantic_analysis',
            'AII_USE_COLORS': 'use_colors',
            'AII_USE_EMOJIS': 'use_emojis',
            'AII_USE_ANIMATIONS': 'use_animations',
            'AII_DEBUG': 'enable_debug_mode',
            'AII_TRACE': 'enable_trace_mode',
            'AII_AUTO_SAVE': 'auto_save_sessions'
        }

        for env_var, field_name in bool_env_map.items():
            if env_var in os.environ:
                value = os.environ[env_var].lower() in ('true', '1', 'yes', 'on')
                setattr(config, field_name, value)

        # Integer environment variables
        if 'AII_MAX_HISTORY' in os.environ:
            try:
                config.max_session_history = int(os.environ['AII_MAX_HISTORY'])
            except ValueError:
                pass

        return config

    @classmethod
    def load(cls, cli_args: Any = None, config_file: Optional[str] = None) -> 'OutputConfig':
        """Load configuration from all sources with proper precedence"""
        # Start with defaults
        config = cls()

        # Apply environment variables (lowest precedence)
        env_config = cls.from_environment()
        config = cls._merge_configs(config, env_config)

        # Apply config file (medium precedence)
        file_config = cls.from_config_file(config_file)
        config = cls._merge_configs(config, file_config)

        # Apply CLI arguments (highest precedence)
        if cli_args:
            cli_config = cls.from_cli_args(cli_args)
            config = cls._merge_configs(config, cli_config)

        return config

    @classmethod
    def _merge_configs(cls, base: 'OutputConfig', override: 'OutputConfig') -> 'OutputConfig':
        """Merge two configurations, preferring override values"""
        # Create a new config with base values
        merged_data = base.__dict__.copy()

        # Override with non-default values from override config
        default_config = cls()
        for key, value in override.__dict__.items():
            # Only override if the value differs from default
            if getattr(default_config, key) != value:
                merged_data[key] = value

        # Create new instance with merged data
        merged = cls()
        for key, value in merged_data.items():
            setattr(merged, key, value)

        return merged

    def save_to_file(self, path: Optional[str] = None) -> bool:
        """Save current configuration to file"""
        if path is None:
            config_dir = Path.home() / ".aii"
            config_dir.mkdir(parents=True, exist_ok=True)
            path = str(config_dir / "output.json")

        try:
            data = {
                'verbosity': self.verbosity.value,
                'output_format': self.output_format.value,
                'show_llm_provider': self.show_llm_provider,
                'show_timing': self.show_timing,
                'show_tokens': self.show_tokens,
                'show_confidence': self.show_confidence,
                'show_session_info': self.show_session_info,
                'show_cost_estimates': self.show_cost_estimates,
                'show_function_pipeline': self.show_function_pipeline,
                'show_artifacts': self.show_artifacts,
                'show_performance_metrics': self.show_performance_metrics,
                'enable_semantic_analysis': self.enable_semantic_analysis,
                'use_colors': self.use_colors,
                'use_emojis': self.use_emojis,
                'use_animations': self.use_animations,
                'enable_debug_mode': self.enable_debug_mode,
                'enable_trace_mode': self.enable_trace_mode,
                'max_session_history': self.max_session_history,
                'auto_save_sessions': self.auto_save_sessions,
                'custom_footer_fields': self.custom_footer_fields,
                'custom_header_fields': self.custom_header_fields
            }

            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            print(f"Warning: Could not save config to {path}: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'verbosity': self.verbosity.value,
            'output_format': self.output_format.value,
            'show_llm_provider': self.show_llm_provider,
            'show_timing': self.show_timing,
            'show_tokens': self.show_tokens,
            'show_confidence': self.show_confidence,
            'show_session_info': self.show_session_info,
            'show_cost_estimates': self.show_cost_estimates,
            'show_function_pipeline': self.show_function_pipeline,
            'show_artifacts': self.show_artifacts,
            'show_performance_metrics': self.show_performance_metrics,
            'enable_semantic_analysis': self.enable_semantic_analysis,
            'use_colors': self.use_colors,
            'use_emojis': self.use_emojis,
            'use_animations': self.use_animations,
            'enable_debug_mode': self.enable_debug_mode,
            'enable_trace_mode': self.enable_trace_mode,
            'max_session_history': self.max_session_history,
            'auto_save_sessions': self.auto_save_sessions,
            'custom_footer_fields': self.custom_footer_fields,
            'custom_header_fields': self.custom_header_fields
        }

    def should_show_semantic_analysis(self) -> bool:
        """Determine if semantic analysis should be enabled"""
        return (
            self.enable_semantic_analysis and
            self.verbosity.value >= self.semantic_analysis_verbosity_threshold.value
        )

    def get_effective_verbosity(self) -> VerbosityLevel:
        """Get the effective verbosity level considering debug mode"""
        if self.enable_debug_mode or self.enable_trace_mode:
            return VerbosityLevel.DETAILED
        return self.verbosity

    def __str__(self) -> str:
        """String representation of configuration"""
        return f"OutputConfig(verbosity={self.verbosity.value}, format={self.output_format.value})"

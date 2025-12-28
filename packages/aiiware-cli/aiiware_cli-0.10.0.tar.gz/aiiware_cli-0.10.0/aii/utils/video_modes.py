# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Video frame extraction modes - Adaptive and Fixed Rate strategies.

This module provides two operational modes for video frame extraction:
- Mode 1: Adaptive Frame Rate - Dynamically adjusts FPS to maintain cost ceiling
- Mode 2: Fixed Frame Rate with Budget - Maintains fixed FPS, limits total frames
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Literal
from dataclasses import dataclass

from aii.utils.video import (
    get_video_duration,
    check_video_has_audio,
    estimate_extraction_cost,
    extract_video_frames
)

DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")


class ExtractionMode(str, Enum):
    """Video frame extraction modes."""
    ADAPTIVE = "adaptive"  # Adjust FPS to maintain cost ceiling
    FIXED_RATE = "fixed_rate"  # Fixed FPS, limit total frames


@dataclass
class ExtractionConfig:
    """Configuration for video frame extraction."""
    mode: ExtractionMode = ExtractionMode.ADAPTIVE
    fps: float = 1.0  # Target FPS (adaptive mode adjusts this)
    max_frames: int = 300  # Hard limit on total frames
    hard_cost_limit: float = 1.00  # Maximum cost in USD
    tokens_per_frame: int = 1000  # Estimated tokens per frame


@dataclass
class ExtractionResult:
    """Result of video frame extraction."""
    frames: list[str]  # Base64-encoded PNG images
    num_frames: int
    actual_fps: float
    estimated_cost: float
    duration: float
    file_size_mb: float
    has_audio: bool
    mode_used: ExtractionMode
    video_path: str  # Temporary file path (caller must cleanup)


def extract_frames_adaptive(
    video_path: str,
    model_name: str,
    input_price_per_million: float,
    config: ExtractionConfig
) -> ExtractionResult:
    """
    Mode 1: Adaptive Frame Rate - Adjust FPS to maintain cost ceiling.

    This mode dynamically reduces FPS to ensure the total cost stays within
    the hard limit, prioritizing coverage over frame rate.

    Args:
        video_path: Path to video file
        model_name: Name of the model being used
        input_price_per_million: Model's input price per million tokens
        config: Extraction configuration

    Returns:
        ExtractionResult with frames and metadata

    Raises:
        RuntimeError: If cost exceeds hard limit even at minimum FPS
    """
    duration = get_video_duration(video_path)
    file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
    has_audio = check_video_has_audio(video_path)

    # Calculate optimal FPS to stay within budget
    estimate = estimate_extraction_cost(
        video_path,
        config.fps,
        input_price_per_million,
        config.max_frames,
        config.tokens_per_frame
    )

    # Check if we need to reduce FPS further to meet cost limit
    if estimate['estimated_cost'] > config.hard_cost_limit:
        # Calculate maximum affordable frames
        max_affordable_frames = int(
            (config.hard_cost_limit * 1_000_000) /
            (config.tokens_per_frame * input_price_per_million)
        )

        if max_affordable_frames < 1:
            raise RuntimeError(
                f"Video extraction cost would exceed ${config.hard_cost_limit:.2f} "
                f"even with minimum sampling. Please use Gemini 2.5 Pro for native video support."
            )

        # Use the lesser of max_frames and max_affordable_frames
        effective_max_frames = min(config.max_frames, max_affordable_frames)

        # Recalculate estimate with new limit
        estimate = estimate_extraction_cost(
            video_path,
            config.fps,
            input_price_per_million,
            effective_max_frames,
            config.tokens_per_frame
        )

    actual_fps = estimate['fps']
    num_frames = estimate['num_frames']

    if DEBUG_MODE:
        print(f"\n📹 DEBUG [Adaptive Frame Extraction]:")
        print(f"   Model: {model_name}")
        print(f"   Video: {duration:.1f}s ({file_size_mb:.1f} MB)")
        print(f"   Mode: Adaptive (auto-adjusted FPS)")
        print(f"   Frames: {num_frames} at {actual_fps:.2f} fps")
        print(f"   Cost: ${estimate['estimated_cost']:.3f}")
        if has_audio:
            print(f"   ⚠️  Audio will be lost in frame extraction")

    # Extract frames
    frames = extract_video_frames(
        video_path,
        fps=actual_fps,
        max_frames=config.max_frames
    )

    return ExtractionResult(
        frames=frames,
        num_frames=len(frames),
        actual_fps=actual_fps,
        estimated_cost=estimate['estimated_cost'],
        duration=duration,
        file_size_mb=file_size_mb,
        has_audio=has_audio,
        mode_used=ExtractionMode.ADAPTIVE,
        video_path=video_path
    )


def extract_frames_fixed_rate(
    video_path: str,
    model_name: str,
    input_price_per_million: float,
    config: ExtractionConfig
) -> ExtractionResult:
    """
    Mode 2: Fixed Frame Rate with Budget - Maintain constant FPS, limit total frames.

    This mode maintains the configured FPS but limits the number of frames
    processed based on the cost budget. Prioritizes consistent sampling over
    full video coverage.

    Args:
        video_path: Path to video file
        model_name: Name of the model being used
        input_price_per_million: Model's input price per million tokens
        config: Extraction configuration

    Returns:
        ExtractionResult with frames and metadata

    Raises:
        RuntimeError: If even one frame exceeds the cost limit
    """
    duration = get_video_duration(video_path)
    file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
    has_audio = check_video_has_audio(video_path)

    # Calculate maximum affordable frames at fixed FPS
    max_affordable_frames = int(
        (config.hard_cost_limit * 1_000_000) /
        (config.tokens_per_frame * input_price_per_million)
    )

    if max_affordable_frames < 1:
        raise RuntimeError(
            f"Cost per frame (${(config.tokens_per_frame * input_price_per_million) / 1_000_000:.3f}) "
            f"exceeds budget (${config.hard_cost_limit:.2f}). "
            f"Please use Gemini 2.5 Pro for native video support."
        )

    # Calculate how many frames we can extract at fixed FPS
    frames_at_fixed_fps = int(duration * config.fps)

    # Use the minimum of: max_frames, max_affordable_frames, frames_at_fixed_fps
    effective_max_frames = min(
        config.max_frames,
        max_affordable_frames,
        frames_at_fixed_fps
    )

    # Calculate actual cost
    estimated_cost = (
        effective_max_frames *
        config.tokens_per_frame *
        input_price_per_million / 1_000_000
    )

    if DEBUG_MODE:
        print(f"\n📹 DEBUG [Fixed Rate Frame Extraction]:")
        print(f"   Model: {model_name}")
        print(f"   Video: {duration:.1f}s ({file_size_mb:.1f} MB)")
        print(f"   Mode: Fixed Rate ({config.fps} fps)")
        print(f"   Frames: {effective_max_frames} (budget-limited)")
        print(f"   Cost: ${estimated_cost:.3f}")
        if effective_max_frames < frames_at_fixed_fps:
            print(f"   ⚠️  Only processing first {effective_max_frames} frames due to budget")
        if has_audio:
            print(f"   ⚠️  Audio will be lost in frame extraction")

    # Extract frames at fixed FPS
    frames = extract_video_frames(
        video_path,
        fps=config.fps,
        max_frames=effective_max_frames
    )

    return ExtractionResult(
        frames=frames,
        num_frames=len(frames),
        actual_fps=config.fps,
        estimated_cost=estimated_cost,
        duration=duration,
        file_size_mb=file_size_mb,
        has_audio=has_audio,
        mode_used=ExtractionMode.FIXED_RATE,
        video_path=video_path
    )


def extract_video_frames_with_mode(
    video_path: str,
    model_name: str,
    input_price_per_million: float,
    mode: Literal["adaptive", "fixed_rate"] = "adaptive",
    fps: float = 1.0,
    max_frames: int = 300,
    hard_cost_limit: float = 1.00
) -> ExtractionResult:
    """
    Extract video frames using specified mode.

    This is the main entry point for mode-based frame extraction.

    Args:
        video_path: Path to video file
        model_name: Name of the model being used
        input_price_per_million: Model's input price per million tokens
        mode: Extraction mode ("adaptive" or "fixed_rate")
        fps: Target frames per second (default: 1.0)
        max_frames: Maximum frames limit (default: 300)
        hard_cost_limit: Maximum cost in USD (default: $1.00)

    Returns:
        ExtractionResult with frames and metadata

    Raises:
        RuntimeError: If extraction fails or exceeds cost limit
    """
    config = ExtractionConfig(
        mode=ExtractionMode(mode),
        fps=fps,
        max_frames=max_frames,
        hard_cost_limit=hard_cost_limit
    )

    if config.mode == ExtractionMode.ADAPTIVE:
        return extract_frames_adaptive(video_path, model_name, input_price_per_million, config)
    else:
        return extract_frames_fixed_rate(video_path, model_name, input_price_per_million, config)


def get_extraction_mode_from_config() -> Literal["adaptive", "fixed_rate"]:
    """
    Get extraction mode from configuration.

    For now, returns default "adaptive" mode.
    Future: Read from ~/.aii/config.yaml

    Returns:
        Extraction mode string
    """
    # TODO: Read from config file in future version
    # from aii.config import get_config
    # config = get_config()
    # return config.get("video_extraction", {}).get("mode", "adaptive")

    return "adaptive"

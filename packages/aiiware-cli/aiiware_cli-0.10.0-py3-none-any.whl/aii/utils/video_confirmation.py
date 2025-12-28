# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
User confirmation flow for video frame extraction.

This module handles the interactive prompt that asks users whether they want
to proceed with frame extraction, showing cost estimates and warnings.
"""

from pathlib import Path
from typing import Optional

import os
from aii.utils.video import (
    check_video_has_audio,
    estimate_extraction_cost,
    get_video_duration
)

DEBUG_MODE = os.getenv("AII_DEBUG", "").lower() in ("1", "true", "yes")


def confirm_frame_extraction(
    video_path: str,
    model_name: str,
    input_price_per_million: float,
    fps: float = 1.0,
    max_frames: Optional[int] = None,
    auto_confirm: bool = False,
    cost_warning_threshold: float = 0.10
) -> bool:
    """
    Show cost estimate and ask user for confirmation.

    Args:
        video_path: Path to video file
        model_name: Name of the model being used
        input_price_per_million: Model's input price per million tokens
        fps: Frames per second (default: 1.0)
        max_frames: Maximum frames limit (optional)
        auto_confirm: Skip confirmation prompt (default: False)
        cost_warning_threshold: Show warning if cost > this value (default: $0.10)

    Returns:
        True if user confirms or auto_confirm=True, False otherwise
    """
    # Get video metadata
    duration = get_video_duration(video_path)
    file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
    has_audio = check_video_has_audio(video_path)

    # Estimate cost
    estimate = estimate_extraction_cost(
        video_path,
        fps,
        input_price_per_million,
        max_frames
    )

    # Auto-confirm if requested
    if auto_confirm:
        print(f"📹 Auto-extracting {estimate['num_frames']} frames from video...")
        return True

    # Build prompt
    print(f"\n⚠️  {model_name} doesn't support direct video upload.")
    print("   Would you like to extract video frames for analysis? (Y/n)\n")
    print("   Details:")
    print(f"   - Video duration: {duration:.1f} seconds")
    print(f"   - File size: {file_size_mb:.1f} MB")
    print(f"   - Estimated frames: {estimate['num_frames']} ({estimate['fps']:.1f} frame/second)")
    print(f"   - Estimated cost: ${estimate['estimated_cost']:.3f}")

    # High cost warning
    if estimate['estimated_cost'] > cost_warning_threshold:
        print(f"\n   ⚠️  HIGH COST WARNING: Estimated cost is ${estimate['estimated_cost']:.2f}")
        print("      Consider using Gemini 2.5 Pro instead (native video support)")

    # Very high cost warning (> $0.50)
    if estimate['estimated_cost'] > 0.50:
        print(f"\n   ⚠️  VERY HIGH COST WARNING: ${estimate['estimated_cost']:.2f}")
        print("      This is expensive! Strongly recommend Gemini 2.5 Pro instead.")

    # Hard limit ($1.00)
    if estimate['estimated_cost'] > 1.00:
        print(f"\n   ❌ ERROR: Estimated cost (${estimate['estimated_cost']:.2f}) exceeds safety limit ($1.00)")
        print("      Please use a shorter video or Gemini 2.5 Pro.")
        return False

    # Audio warning
    if has_audio:
        print("\n   ⚠️  Note: Video contains audio, which will be lost in frame extraction.")
        print("      For audio+video analysis, use Gemini 2.5 Pro instead.")

    # FPS adjustment notice
    if max_frames and (duration * fps) > max_frames:
        print(f"\n   ℹ️  FPS reduced to {estimate['fps']:.2f} to stay within {max_frames} frame limit")

    print()

    # Get user input
    try:
        response = input("> ").strip().lower()
        return response in ["y", "yes", ""]  # Default to yes if empty
    except (EOFError, KeyboardInterrupt):
        print("\nFrame extraction cancelled.")
        return False


def validate_extraction_cost(
    video_path: str,
    model_name: str,
    input_price_per_million: float,
    fps: float = 1.0,
    max_frames: Optional[int] = 300,
    hard_limit: float = 1.00
) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    Validate whether frame extraction should proceed (non-interactive).

    Used in server/API contexts where interactive prompts aren't possible.
    Checks cost against hard limit and returns estimation details.

    Args:
        video_path: Path to video file
        model_name: Name of the model being used
        input_price_per_million: Model's input price per million tokens
        fps: Frames per second (default: 1.0)
        max_frames: Maximum frames limit (default: 300)
        hard_limit: Maximum allowed cost in USD (default: $1.00)

    Returns:
        Tuple of (should_proceed, estimate_dict, error_message)
        - should_proceed: True if extraction should proceed, False otherwise
        - estimate_dict: Cost estimation details (None if validation failed)
        - error_message: Error message if validation failed (None if OK)
    """
    try:
        # Get video metadata
        duration = get_video_duration(video_path)
        file_size_mb = Path(video_path).stat().st_size / (1024 * 1024)
        has_audio = check_video_has_audio(video_path)

        # Estimate cost
        estimate = estimate_extraction_cost(
            video_path,
            fps,
            input_price_per_million,
            max_frames
        )

        # Check hard limit
        if estimate['estimated_cost'] > hard_limit:
            error_msg = (
                f"Frame extraction cost (${estimate['estimated_cost']:.2f}) exceeds "
                f"safety limit (${hard_limit:.2f}). Video duration: {duration:.1f}s, "
                f"estimated frames: {estimate['num_frames']}. "
                f"Please use a shorter video or Gemini 2.5 Pro (native video support)."
            )
            return False, None, error_msg

        # Log details in debug mode
        if DEBUG_MODE:
            print(f"\n📹 DEBUG [Frame Extraction Validation]:")
            print(f"   Model: {model_name}")
            print(f"   Video duration: {duration:.1f}s ({file_size_mb:.1f} MB)")
            print(f"   Estimated frames: {estimate['num_frames']} at {estimate['fps']:.1f} fps")
            print(f"   Estimated cost: ${estimate['estimated_cost']:.3f}")
            print(f"   Has audio: {has_audio}")
            if has_audio:
                print(f"   ⚠️  Warning: Audio will be lost in frame extraction")

        # Add metadata to estimate
        estimate['duration'] = duration
        estimate['file_size_mb'] = file_size_mb
        estimate['has_audio'] = has_audio
        estimate['model_name'] = model_name

        return True, estimate, None

    except Exception as e:
        error_msg = f"Failed to validate frame extraction: {e}"
        return False, None, error_msg

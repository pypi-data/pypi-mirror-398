# Copyright 2025-present AiiWare.com. All Rights Reserved.
#
# This source code is proprietary and confidential to AiiWare.com.
# Unauthorized copying, modification, distribution, or use is strictly
# prohibited without prior written permission.

"""
Video processing utilities for frame extraction and metadata.

This module provides functionality to extract frames from videos for models
that support image analysis but not direct video upload (e.g., GPT-4o, Claude).
"""

import base64
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def check_ffmpeg_installed() -> bool:
    """
    Check if ffmpeg is installed and available.

    Returns:
        True if ffmpeg is installed, False otherwise
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
            timeout=5
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def save_base64_video(base64_data: str, mime_type: str) -> str:
    """
    Save base64-encoded video data to temporary file.

    Args:
        base64_data: Base64-encoded video data
        mime_type: Video MIME type (e.g., 'video/mp4')

    Returns:
        Path to temporary video file (caller responsible for cleanup)

    Raises:
        RuntimeError: If saving fails
    """
    # Determine file extension from MIME type
    extension_map = {
        "video/mp4": ".mp4",
        "video/mpeg": ".mpeg",
        "video/mov": ".mov",
        "video/avi": ".avi",
        "video/webm": ".webm",
        "video/quicktime": ".mov"
    }
    extension = extension_map.get(mime_type, ".mp4")

    try:
        # Decode base64 data
        video_data = base64.b64decode(base64_data)

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as tmp_file:
            tmp_file.write(video_data)
            return tmp_file.name

    except Exception as e:
        raise RuntimeError(f"Failed to save video to temporary file: {e}") from e


def get_video_duration(video_path: str) -> float:
    """
    Get video duration in seconds using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Duration in seconds

    Raises:
        RuntimeError: If ffprobe fails or ffmpeg not installed
    """
    if not check_ffmpeg_installed():
        raise RuntimeError(
            "ffmpeg is required for video frame extraction. "
            "Install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
        )

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=10
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        raise RuntimeError(f"Failed to get video duration: {e}") from e


def check_video_has_audio(video_path: str) -> bool:
    """
    Check if video has audio track.

    Args:
        video_path: Path to video file

    Returns:
        True if video has audio, False otherwise
    """
    if not check_ffmpeg_installed():
        return False

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_type",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path
            ],
            capture_output=True,
            check=True,
            text=True,
            timeout=10
        )
        return "audio" in result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def extract_video_frames(
    video_path: str,
    fps: float = 1.0,
    max_frames: Optional[int] = None
) -> list[str]:
    """
    Extract frames from video at specified FPS.

    Args:
        video_path: Path to video file
        fps: Frames per second to extract (default: 1.0)
        max_frames: Maximum number of frames to extract (optional)

    Returns:
        List of base64-encoded PNG images

    Raises:
        RuntimeError: If ffmpeg not installed or extraction fails
    """
    if not check_ffmpeg_installed():
        raise RuntimeError(
            "ffmpeg is required for video frame extraction. "
            "Install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Ubuntu)"
        )

    # Adjust FPS if max_frames specified
    if max_frames:
        duration = get_video_duration(video_path)
        estimated_frames = int(duration * fps)
        if estimated_frames > max_frames:
            fps = max_frames / duration

    # Create temporary directory for frames
    with tempfile.TemporaryDirectory() as tmpdir:
        output_pattern = str(Path(tmpdir) / "frame_%04d.png")

        # Use ffmpeg to extract frames
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-q:v", "2",  # High quality (scale 2-31, lower is better)
            "-frames:v", str(max_frames) if max_frames else "999999",
            output_pattern
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=120  # 2 minute timeout
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to extract frames: {e.stderr.decode() if e.stderr else str(e)}"
            ) from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("Frame extraction timed out (> 2 minutes)")

        # Read frames and encode as base64
        frames = []
        frame_files = sorted(Path(tmpdir).glob("frame_*.png"))

        if not frame_files:
            raise RuntimeError("No frames were extracted from video")

        for frame_path in frame_files:
            with open(frame_path, "rb") as f:
                base64_data = base64.b64encode(f.read()).decode()
                frames.append(base64_data)

        return frames


def estimate_frame_count(video_path: str, fps: float, max_frames: Optional[int] = None) -> int:
    """
    Estimate number of frames that will be extracted.

    Args:
        video_path: Path to video file
        fps: Frames per second
        max_frames: Maximum frames limit (optional)

    Returns:
        Estimated number of frames
    """
    duration = get_video_duration(video_path)
    estimated = int(duration * fps)

    if max_frames and estimated > max_frames:
        return max_frames

    return estimated


def estimate_extraction_cost(
    video_path: str,
    fps: float,
    input_price_per_million: float,
    max_frames: Optional[int] = None,
    tokens_per_frame: int = 1000
) -> dict:
    """
    Estimate cost of frame extraction.

    Args:
        video_path: Path to video file
        fps: Frames per second
        input_price_per_million: Model's input price per million tokens
        max_frames: Maximum frames limit (optional)
        tokens_per_frame: Estimated tokens per frame (default: 1000 for high-detail images)

    Returns:
        Dictionary with cost estimation details
    """
    duration = get_video_duration(video_path)
    num_frames = estimate_frame_count(video_path, fps, max_frames)

    total_tokens = num_frames * tokens_per_frame
    input_price_per_token = input_price_per_million / 1_000_000
    estimated_cost = total_tokens * input_price_per_token

    # Adjust FPS if limited by max_frames
    actual_fps = fps
    if max_frames and (duration * fps) > max_frames:
        actual_fps = max_frames / duration

    return {
        "duration": duration,
        "num_frames": num_frames,
        "fps": actual_fps,
        "estimated_cost": estimated_cost,
        "tokens_per_frame": tokens_per_frame,
        "total_tokens": total_tokens
    }


def enhance_prompt_for_frames(original_prompt: str, num_frames: int, fps: float) -> str:
    """
    Add context about frame extraction to user's prompt.

    Args:
        original_prompt: User's original prompt
        num_frames: Number of frames extracted
        fps: Frames per second used

    Returns:
        Enhanced prompt with frame context
    """
    context = (
        f"[Video Analysis Context: The following {num_frames} images are frames "
        f"extracted from a video at {fps} frame(s) per second. "
        f"Analyze them sequentially to understand the video content.]\n\n"
    )
    return context + original_prompt

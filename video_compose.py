"""
Video composition.

Takes a gameplay clip, a narration WAV and the narrated text, then produces a
captioned vertical video: a random segment of the gameplay with the narration
muxed in and word-by-word captions burned on with ffmpeg's subtitles filter.

All external commands are invoked via subprocess with argument lists (no shell),
so there is no command-injection surface and it runs identically on Linux and
Windows (no bash dependency).
"""

import json
import logging
import os
import random
import subprocess

import captions

logger = logging.getLogger(__name__)

FALLBACK_WIDTH, FALLBACK_HEIGHT = 1080, 1920


def _run(cmd, **kwargs):
    """Run a command, returning the CompletedProcess (captured output)."""
    logger.info("Running: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def probe_dimensions(video_path):
    """Return (width, height) of ``video_path`` via ffprobe, with a fallback."""
    result = _run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", video_path,
    ])
    try:
        stream = json.loads(result.stdout)["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (KeyError, IndexError, ValueError, json.JSONDecodeError):
        logger.warning("Could not probe video dimensions; using %dx%d", FALLBACK_WIDTH, FALLBACK_HEIGHT)
        return FALLBACK_WIDTH, FALLBACK_HEIGHT


def probe_duration(media_path):
    """Return duration in seconds of ``media_path`` via ffprobe (0.0 on failure)."""
    result = _run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", media_path,
    ])
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return 0.0


def _pick_start_offset(video_duration, clip_duration):
    """Pick a random start offset so the clip fits within the gameplay video."""
    if video_duration <= 0:
        return 0.0
    latest_start = video_duration - clip_duration - 1
    if latest_start <= 10:
        return max(0.0, min(10.0, video_duration - clip_duration))
    return random.uniform(10.0, latest_start)


def compose_video(text, audio_path, source_video, output_path, audio_duration=None):
    """
    Build a captioned video from ``source_video`` + ``audio_path`` + ``text``.

    Args:
        text (str): The narrated text (used for caption words).
        audio_path (str): Narration WAV path.
        source_video (str): Gameplay video path.
        output_path (str): Destination MP4 path.
        audio_duration (float, optional): Narration duration; probed if omitted.

    Returns:
        dict: {} on success, {"error": "..."} on failure.
    """
    if not os.path.exists(source_video):
        return {"error": f"Source video not found: {source_video}"}
    if not os.path.exists(audio_path):
        return {"error": f"Audio file not found: {audio_path}"}

    if audio_duration is None:
        audio_duration = probe_duration(audio_path)
    if audio_duration <= 0:
        return {"error": "Could not determine narration duration"}

    width, height = probe_dimensions(source_video)
    video_duration = probe_duration(source_video)
    start_offset = _pick_start_offset(video_duration, audio_duration)

    # Build the caption file next to the output (plain relative name so ffmpeg's
    # subtitles filter needs no path escaping).
    ass_path = os.path.splitext(os.path.basename(output_path))[0] + ".ass"
    word_timings = captions.compute_word_timings(text, audio_path, audio_duration)
    captions.write_ass(word_timings, ass_path, width, height)

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_offset:.3f}", "-i", source_video,
        "-i", audio_path,
        "-t", f"{audio_duration:.3f}",
        "-vf", f"subtitles={ass_path}",
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]
    result = _run(cmd)
    try:
        if result.returncode != 0:
            logger.error("ffmpeg failed: %s", result.stderr[-1000:])
            return {"error": f"Video composition failed (ffmpeg exit {result.returncode})"}
        if not os.path.exists(output_path) or os.path.getsize(output_path) < 1024:
            return {"error": "Video composition produced no output"}
        return {}
    finally:
        if os.path.exists(ass_path):
            os.remove(ass_path)

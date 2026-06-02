"""
Video generation pipeline orchestrator.

Flow: extract + clean text -> split into sections -> per section synthesize TTS,
adjust speed, build a captioned clip over gameplay footage -> concatenate the
section clips into the final video.

All shelling out uses subprocess argument lists (no shell, no bash scripts).
"""

import logging
import os
import random
import shutil
import subprocess
import sys

import captions  # noqa: F401  (kept importable for callers/tests)
import video_compose
from cleantext import cleantext
from content import extract_text, is_url
from text_splitter import split_text_into_sections
from text_to_speech import generate_wav

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

MIN_WORDS = 10
MIN_SOURCE_BYTES = 50 * 1024 * 1024  # Source gameplay clips should be large.


def get_source_video(source_path=None):
    """
    Resolve a gameplay video: a file is used directly; a directory yields a
    random large .mp4 from within it.

    Returns the path (str) or {"error": ...}.
    """
    source_path = source_path or os.getenv("SOURCE_VIDEO_DIR", "static")
    try:
        if os.path.isfile(source_path):
            if not source_path.lower().endswith(".mp4"):
                return {"error": f"Invalid video format (expected .mp4): {source_path}"}
            return source_path

        if os.path.isdir(source_path):
            candidates = []
            for name in os.listdir(source_path):
                if not name.lower().endswith(".mp4"):
                    continue
                full = os.path.join(source_path, name)
                try:
                    if os.path.getsize(full) > MIN_SOURCE_BYTES:
                        candidates.append(full)
                    else:
                        logger.warning("Skipping small video file: %s", name)
                except OSError:
                    continue
            if not candidates:
                return {"error": f'No usable .mp4 gameplay videos found in "{source_path}"'}
            chosen = random.choice(candidates)
            logger.info("Selected gameplay video: %s", chosen)
            return chosen

        return {"error": f"Source path not found: {source_path}"}
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"Error selecting source video: {exc}"}


def _atempo_chain(speed_factor):
    """
    Build an ffmpeg atempo filter string for an arbitrary speed factor.

    A single atempo only supports 0.5-2.0, so factors outside that are split
    into a chain of in-range multipliers.
    """
    factor = max(speed_factor, 0.25)
    multipliers = []
    while factor > 2.0:
        multipliers.append(2.0)
        factor /= 2.0
    while factor < 0.5:
        multipliers.append(0.5)
        factor /= 0.5
    multipliers.append(factor)
    return ",".join(f"atempo={m:.4f}" for m in multipliers)


def speed_up_audio(input_file, output_file, speed_factor):
    """Apply a playback-speed change to ``input_file`` with ffmpeg atempo."""
    if not os.path.exists(input_file):
        return {"error": f"Input audio file missing: {input_file}"}
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-filter:a", _atempo_chain(speed_factor), "-vn", output_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("atempo failed: %s", result.stderr[-500:])
        return {"error": f"Audio speed adjustment failed (ffmpeg exit {result.returncode})"}
    return {"success": output_file}


def script(input_text, customspeed, customvoice, final_path="final.mp4",
           progress_queue=None, backend=None):
    """
    Generate a captioned video from text/URL input.

    Args:
        input_text (str): Article URL or raw text.
        customspeed (float): Narration speed multiplier.
        customvoice (str): Backend-native voice id.
        final_path (str): Destination MP4 path.
        progress_queue (queue.Queue, optional): For SSE progress updates.
        backend (str, optional): TTS backend override (tiktok/elevenlabs/remote).

    Returns:
        dict: {"success": ...} or {"error": ...}.
    """

    def update_progress(progress, step, message):
        if progress_queue:
            try:
                progress_queue.put({"progress": progress, "step": step, "message": message})
            except Exception:
                pass

    def process_section(section_text, index, total, source_video):
        suffix = f"_section_{index}" if total > 1 else ""
        raw_wav = f"output{suffix}.wav"
        fast_wav = f"output_fast{suffix}.wav"
        section_video = f"section_{index}.mp4"

        update_progress(_section_progress(index, total, 0.1), "audio",
                        f"Generating speech for section {index}/{total}...")
        tts_result = generate_wav(section_text, customvoice, raw_wav, backend=backend)
        if tts_result and "error" in tts_result:
            return {"error": f"TTS failed for section {index}: {tts_result['error']}"}

        update_progress(_section_progress(index, total, 0.3), "audio",
                        f"Adjusting speed for section {index}...")
        speed_result = speed_up_audio(raw_wav, fast_wav, customspeed)
        if "error" in speed_result:
            return speed_result

        update_progress(_section_progress(index, total, 0.5), "video",
                        f"Creating captioned video for section {index}/{total}...")
        duration = video_compose.probe_duration(fast_wav)
        compose_result = video_compose.compose_video(
            section_text, fast_wav, source_video, section_video, audio_duration=duration
        )
        if "error" in compose_result:
            return {"error": f"Video creation failed for section {index}: {compose_result['error']}"}

        for temp in (raw_wav, fast_wav):
            if os.path.exists(temp):
                os.remove(temp)
        return {"success": section_video}

    def _section_progress(index, total, fraction):
        per = 70.0 / total
        return int(15 + (index - 1) * per + fraction * per)

    try:
        update_progress(2, "validation", "Reading and cleaning input...")
        if is_url(input_text):
            update_progress(4, "validation", "Extracting article text from URL...")
        text = cleantext(extract_text(input_text))

        word_count = len(text.split())
        if word_count < MIN_WORDS:
            return {"error": f"Need at least {MIN_WORDS} words to narrate (found {word_count})."}

        update_progress(6, "setup", "Planning sections...")
        sections = split_text_into_sections(text)
        total = len(sections)
        logger.info("Split into %d section(s)", total)

        update_progress(10, "setup", "Selecting background gameplay video...")
        source_video = get_source_video()
        if isinstance(source_video, dict) and "error" in source_video:
            return source_video

        section_videos = []
        for index, section_text in enumerate(sections, 1):
            result = process_section(section_text, index, total, source_video)
            if "error" in result:
                return result
            section_videos.append(result["success"])

        update_progress(88, "merge", "Assembling final video...")
        _assemble(section_videos, final_path)

        if not os.path.exists(final_path):
            return {"error": f"Final video was not created at {final_path}"}

        update_progress(100, "completed", f"Done — {total} section(s) processed.")
        return {"success": f"Video generated with {total} section(s)."}

    except ValueError as exc:
        return {"error": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Pipeline failure")
        return {"error": f"Video generation failed: {exc}"}


def _assemble(section_videos, final_path):
    """Move a single section to ``final_path`` or concat multiple with ffmpeg."""
    if not section_videos:
        raise RuntimeError("No section videos were produced")

    if len(section_videos) == 1:
        shutil.move(section_videos[0], final_path)
        return

    list_file = "section_list.txt"
    with open(list_file, "w", encoding="utf-8") as handle:
        for video in section_videos:
            handle.write(f"file '{os.path.abspath(video)}'\n")
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
             "-c", "copy", final_path],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg concat failed: {result.stderr[-500:]}")
    finally:
        for video in section_videos:
            if os.path.exists(video):
                os.remove(video)
        if os.path.exists(list_file):
            os.remove(list_file)


if __name__ == "__main__":
    sample = "This is a test sentence that should contain at least ten words for narration."
    print(script(sample, 1.0, "en_us_006"))

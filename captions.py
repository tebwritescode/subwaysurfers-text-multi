"""
Caption timing and rendering.

Produces an ASS subtitle file that displays the narrated text one word at a
time, centered TikTok-style. Word timings come from one of two sources:

  - Whisper ASR server (optional): if WHISPER_ASR_URL is set, real word-level
    timestamps are fetched from a self-hosted whisper-asr-webservice instance.
  - Estimation (default): words are spread across the audio duration weighted
    by word length. Requires no external services and works offline.

The ASS file is later burned onto the gameplay video by video_compose.py via
ffmpeg's subtitles filter (no OpenCV / moviepy needed).
"""

import logging
import os

logger = logging.getLogger(__name__)

# Caption styling (ASS). Sizes are relative to a 1080-wide reference and scaled
# to the actual video resolution when the file is written.
FONT_NAME = os.getenv("CAPTION_FONT", "DejaVu Sans")
# Shift captions slightly earlier so they appear just before the word is spoken.
DEFAULT_TIMING_OFFSET = float(os.getenv("CAPTION_TIMING_OFFSET", "0.0"))


def estimate_word_timings(text, total_duration):
    """
    Spread the words of ``text`` across ``total_duration`` seconds.

    Longer words are given proportionally more on-screen time. Returns a list of
    ``(word, start_seconds, end_seconds)`` tuples.
    """
    words = text.split()
    if not words or total_duration <= 0:
        return []

    weights = [max(len(w), 1) for w in words]
    total_weight = sum(weights)

    timings, elapsed = [], 0.0
    for word, weight in zip(words, weights):
        span = total_duration * (weight / total_weight)
        timings.append((word, elapsed, elapsed + span))
        elapsed += span
    return timings


def whisper_word_timings(audio_path, server_url):
    """
    Fetch real word timestamps from a whisper-asr-webservice server.

    Returns a list of ``(word, start, end)`` or raises on failure.
    """
    import requests

    endpoint = f"{server_url.rstrip('/')}/asr"
    with open(audio_path, "rb") as audio:
        response = requests.post(
            endpoint,
            files={"audio_file": audio},
            params={
                "task": "transcribe",
                "language": "en",
                "word_timestamps": "true",
                "output": "json",
            },
            timeout=300,
        )
    if response.status_code != 200:
        raise RuntimeError(f"Whisper ASR error {response.status_code}: {response.text[:200]}")

    result = response.json()
    segments = result.get("segments", [])
    timings = []
    for segment in segments:
        for word in segment.get("words", []):
            token = (word.get("word") or "").strip()
            if token:
                timings.append((token, float(word.get("start", 0)), float(word.get("end", 0))))
    if not timings and result.get("words"):
        for word in result["words"]:
            token = (word.get("word") or "").strip()
            if token:
                timings.append((token, float(word.get("start", 0)), float(word.get("end", 0))))
    return timings


def compute_word_timings(text, audio_path, duration):
    """
    Compute word timings, preferring a Whisper ASR server when configured and
    falling back to estimation on any failure.
    """
    server_url = os.getenv("WHISPER_ASR_URL")
    if server_url:
        try:
            timings = whisper_word_timings(audio_path, server_url)
            if timings:
                logger.info("Using Whisper ASR word timings (%d words)", len(timings))
                return timings
            logger.warning("Whisper ASR returned no words; estimating timings instead")
        except Exception as exc:
            logger.warning("Whisper ASR unavailable (%s); estimating timings instead", exc)
    return estimate_word_timings(text, duration)


def _ass_timestamp(seconds):
    """Format ``seconds`` as an ASS timestamp H:MM:SS.cc."""
    seconds = max(seconds, 0.0)
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis == 100:  # rounding overflow
        secs += 1
        centis = 0
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _escape(text):
    """Escape characters special to ASS dialogue lines."""
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def write_ass(word_timings, output_path, video_width, video_height, timing_offset=None):
    """
    Write an ASS subtitle file showing one word at a time, centered.

    Args:
        word_timings (list): ``(word, start, end)`` tuples.
        output_path (str): Destination .ass path.
        video_width (int), video_height (int): Source video resolution.
        timing_offset (float, optional): Seconds to shift captions earlier.
    """
    if timing_offset is None:
        timing_offset = DEFAULT_TIMING_OFFSET

    font_size = max(int(video_height * 0.07), 24)
    outline = max(int(font_size * 0.12), 2)

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{FONT_NAME},{font_size},&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{outline},2,5,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]
    for word, start, end in word_timings:
        start = max(start - timing_offset, 0.0)
        end = max(end - timing_offset, start + 0.05)
        text = _escape(word.strip().upper())
        if not text:
            continue
        lines.append(
            f"Dialogue: 0,{_ass_timestamp(start)},{_ass_timestamp(end)},Caption,,0,0,0,,{text}\n"
        )

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.writelines(lines)
    logger.info("Wrote %d caption events to %s", len(word_timings), output_path)
    return output_path

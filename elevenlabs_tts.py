"""
ElevenLabs text-to-speech backend.

Talks to the ElevenLabs HTTP API directly (no SDK dependency). Requires the
ELEVENLABS_API_KEY environment variable. Receives already-extracted plain text
(URL handling happens upstream in content.py).
"""

import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

API_BASE = "https://api.elevenlabs.io/v1"
# A widely-available stock voice used when no specific voice is selected.
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
MODEL_ID = "eleven_monolingual_v1"
MAX_CHUNK_CHARS = 2000  # Conservative per-request character limit.


def _api_key():
    key = os.getenv("ELEVENLABS_API_KEY")
    if key and key != "your_elevenlabs_api_key_here":
        return key
    return None


def list_elevenlabs_voices():
    """
    List the voices available to the configured ElevenLabs account.

    Returns:
        dict: {"voices": [{"id", "name", "category"}, ...]} or {"error": "..."}.
    """
    api_key = _api_key()
    if not api_key:
        return {"error": "ElevenLabs API key not configured"}

    try:
        response = requests.get(
            f"{API_BASE}/voices",
            headers={"Accept": "application/json", "xi-api-key": api_key},
            timeout=15,
        )
    except requests.RequestException as exc:
        return {"error": f"Failed to reach ElevenLabs: {exc}"}

    if response.status_code != 200:
        return {"error": f"ElevenLabs API error: {response.status_code} - {response.text}"}

    voices = [
        {
            "id": voice["voice_id"],
            "name": voice["name"],
            "category": voice.get("category", "unknown"),
        }
        for voice in response.json().get("voices", [])
    ]
    return {"voices": voices}


# Backwards-compatible alias (older callers used this name).
get_elevenlabs_voices = list_elevenlabs_voices


def _resolve_voice_id(voice):
    """Return a usable ElevenLabs voice id, falling back to a sensible default."""
    if voice and voice != "default":
        return voice
    result = list_elevenlabs_voices()
    if result.get("voices"):
        return result["voices"][0]["id"]
    return DEFAULT_VOICE_ID


def _chunk_text(text, limit=MAX_CHUNK_CHARS):
    """Split ``text`` into <= ``limit`` character chunks on word boundaries."""
    if len(text) <= limit:
        return [text]
    chunks, current = [], ""
    for word in text.split():
        if current and len(current) + len(word) + 1 > limit:
            chunks.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    if current:
        chunks.append(current)
    return chunks


def generate_wav_elevenlabs(text, voice, output_file):
    """
    Synthesize ``text`` to a WAV file using ElevenLabs.

    Args:
        text (str): Plain text to narrate (already extracted/cleaned).
        voice (str): ElevenLabs voice id (or "default" / falsy for a default).
        output_file (str): Destination WAV path.

    Returns:
        dict: {} on success, {"error": "..."} on failure.
    """
    api_key = _api_key()
    if not api_key:
        return {"error": "ElevenLabs API key not configured. Set ELEVENLABS_API_KEY."}

    text = (text or "").strip()
    if not text:
        return {"error": "No text content to process"}

    voice_id = _resolve_voice_id(voice)
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }

    temp_files = []
    try:
        for index, chunk in enumerate(_chunk_text(text)):
            if not chunk.strip():
                continue
            response = requests.post(
                f"{API_BASE}/text-to-speech/{voice_id}",
                json={
                    "text": chunk,
                    "model_id": MODEL_ID,
                    "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                },
                headers=headers,
                timeout=60,
            )
            if response.status_code != 200:
                return {"error": f"ElevenLabs API error: {response.status_code} - {response.text}"}
            temp_path = f"temp_chunk_{index}.mp3"
            with open(temp_path, "wb") as handle:
                handle.write(response.content)
            temp_files.append(temp_path)

        if not temp_files:
            return {"error": "No audio segments were generated"}

        from pydub import AudioSegment

        combined = AudioSegment.empty()
        for path in temp_files:
            combined += AudioSegment.from_mp3(path)
        combined.export(output_file, format="wav")
        return {}

    except requests.RequestException as exc:
        return {"error": f"Text-to-speech request failed: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"ElevenLabs synthesis failed: {exc}"}
    finally:
        for path in temp_files:
            if os.path.exists(path):
                os.remove(path)

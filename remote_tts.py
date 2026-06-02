"""
Remote text-to-speech backend.

Delegates synthesis to a self-hosted TTS server you run elsewhere (e.g. another
Docker container), mirroring the external-server pattern used for Whisper ASR.

Contract (configurable via env vars):
  - POST {REMOTE_TTS_URL}            JSON {"text": ..., "voice": ...}
        -> audio bytes (audio/wav or audio/mpeg)
  - GET  {REMOTE_TTS_VOICES_URL}     (defaults to "{REMOTE_TTS_URL}/voices")
        -> {"voices": [{"id": ..., "name": ...}, ...]}
"""

import logging
import os

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _base_url():
    return (os.getenv("REMOTE_TTS_URL") or "").rstrip("/")


def _voices_url():
    explicit = os.getenv("REMOTE_TTS_VOICES_URL")
    if explicit:
        return explicit
    base = _base_url()
    return f"{base}/voices" if base else ""


def list_remote_voices():
    """List voices advertised by the remote TTS server (best effort)."""
    url = _voices_url()
    if not url:
        return {"error": "REMOTE_TTS_URL not configured"}
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return {"error": f"Remote TTS voices error: {response.status_code}"}
        data = response.json()
    except requests.RequestException as exc:
        return {"error": f"Failed to reach remote TTS server: {exc}"}
    except ValueError:
        return {"error": "Remote TTS server returned invalid JSON for voices"}

    voices = data.get("voices", data) if isinstance(data, dict) else data
    normalized = []
    for voice in voices or []:
        if isinstance(voice, dict):
            vid = voice.get("id") or voice.get("voice_id") or voice.get("name")
            normalized.append(
                {"id": vid, "name": voice.get("name", vid), "category": "remote"}
            )
        else:  # plain string id
            normalized.append({"id": voice, "name": voice, "category": "remote"})
    return {"voices": normalized}


def generate_wav_remote(text, voice, output_file):
    """
    Synthesize ``text`` by POSTing to the remote TTS server.

    Returns:
        dict: {} on success, {"error": "..."} on failure.
    """
    url = _base_url()
    if not url:
        return {"error": "REMOTE_TTS_URL not configured"}

    text = (text or "").strip()
    if not text:
        return {"error": "No text content to process"}

    try:
        response = requests.post(
            url, json={"text": text, "voice": voice}, timeout=120
        )
    except requests.RequestException as exc:
        return {"error": f"Remote TTS request failed: {exc}"}

    if response.status_code != 200:
        return {"error": f"Remote TTS error: {response.status_code} - {response.text[:200]}"}

    content_type = response.headers.get("Content-Type", "")
    try:
        if "wav" in content_type or output_file.endswith(".wav") and "mpeg" not in content_type:
            with open(output_file, "wb") as handle:
                handle.write(response.content)
            # Re-encode through pydub to guarantee a valid PCM WAV.
            from pydub import AudioSegment

            AudioSegment.from_file(output_file).export(output_file, format="wav")
        else:
            temp_path = "temp_remote_audio"
            with open(temp_path, "wb") as handle:
                handle.write(response.content)
            from pydub import AudioSegment

            AudioSegment.from_file(temp_path).export(output_file, format="wav")
            if os.path.exists(temp_path):
                os.remove(temp_path)
        return {}
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"Failed to save remote TTS audio: {exc}"}

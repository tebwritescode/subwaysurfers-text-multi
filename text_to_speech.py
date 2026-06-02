"""
Text-to-speech dispatcher.

Selects between the available TTS backends. The backend can be chosen per
request (e.g. from the UI dropdown) or globally via the TTS_BACKEND environment
variable. Backends all share the same interface:

    generate_wav_<backend>(text, voice, output_file) -> {} | {"error": ...}
    list_<backend>_voices() -> {"voices": [{"id", "name", "category"}], "error"?}

Backends receive already-extracted, cleaned plain text (see content.py /
cleantext.py), so they are concerned only with text -> audio.
"""

import logging
import os

from elevenlabs_tts import generate_wav_elevenlabs, list_elevenlabs_voices
from remote_tts import generate_wav_remote, list_remote_voices
from tiktokvoice import generate_wav_tiktok, list_tiktok_voices

logger = logging.getLogger(__name__)

DEFAULT_BACKEND = "tiktok"  # Works with no API keys.

# backend name -> (synthesize fn, list-voices fn, human label)
BACKENDS = {
    "tiktok": (generate_wav_tiktok, list_tiktok_voices, "TikTok (free)"),
    "elevenlabs": (generate_wav_elevenlabs, list_elevenlabs_voices, "ElevenLabs (API key)"),
    "remote": (generate_wav_remote, list_remote_voices, "Remote TTS server"),
}


def resolve_backend(requested=None):
    """Resolve the effective backend name from a request value or env, with fallback."""
    backend = (requested or os.getenv("TTS_BACKEND") or DEFAULT_BACKEND).strip().lower()
    if backend not in BACKENDS:
        logger.warning("Unknown TTS backend %r, falling back to %s", backend, DEFAULT_BACKEND)
        backend = DEFAULT_BACKEND
    return backend


def available_backends():
    """Return [{"id", "name", "is_default"}] for populating the UI selector."""
    default = resolve_backend()
    return [
        {"id": name, "name": label, "is_default": name == default}
        for name, (_synth, _voices, label) in BACKENDS.items()
    ]


def list_voices(backend=None):
    """Return the available voices for ``backend`` (default: resolved backend)."""
    backend = resolve_backend(backend)
    _synth, list_fn, _label = BACKENDS[backend]
    result = list_fn()
    result["backend"] = backend
    return result


def generate_wav(text, voice, output_file, backend=None):
    """
    Synthesize ``text`` to ``output_file`` (WAV) using the selected backend.

    Args:
        text (str): Plain narratable text (already extracted/cleaned).
        voice (str): Backend-native voice id.
        output_file (str): Destination WAV path.
        backend (str, optional): Backend override; defaults to TTS_BACKEND env.

    Returns:
        dict: {} on success, {"error": "..."} on failure.
    """
    backend = resolve_backend(backend)
    synth_fn, _list_fn, _label = BACKENDS[backend]
    logger.info("Synthesizing %d chars with backend=%s voice=%s", len(text or ""), backend, voice)
    return synth_fn(text, voice, output_file)

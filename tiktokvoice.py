# TikTok text-to-speech backend.
#
# Uses free public TikTok-TTS relay endpoints (no API key required). Based on
# the community "TikTok-Voice-TTS" project (author: Giorgio), trimmed to a
# server/Docker context and wrapped with helpers used by the TTS dispatcher.

import base64
import logging
import os
import re
from threading import Thread

import requests

logger = logging.getLogger(__name__)

# Public relay endpoints with their respective base64 response keys. They are
# tried in order until one succeeds.
ENDPOINT_DATA = [
    {"url": "https://tiktok-tts.weilnet.workers.dev/api/generation", "response": "data"},
    {"url": "https://countik.com/api/text/speech", "response": "v_data"},
    {"url": "https://gesserit.co/api/tiktok-tts", "response": "base64"},
]

# Available voices with human-friendly labels for the UI dropdown.
VOICE_LABELS = {
    # Disney / character voices
    "en_us_ghostface": "Ghost Face", "en_us_chewbacca": "Chewbacca",
    "en_us_c3po": "C-3PO", "en_us_stitch": "Stitch",
    "en_us_stormtrooper": "Stormtrooper", "en_us_rocket": "Rocket",
    # English
    "en_au_001": "English AU - Female", "en_au_002": "English AU - Male",
    "en_uk_001": "English UK - Male 1", "en_uk_003": "English UK - Male 2",
    "en_us_001": "English US - Female 1", "en_us_002": "English US - Female 2",
    "en_us_006": "English US - Male 1", "en_us_007": "English US - Male 2",
    "en_us_009": "English US - Male 3", "en_us_010": "English US - Male 4",
    # Europe
    "fr_001": "French - Male 1", "fr_002": "French - Male 2",
    "de_001": "German - Female", "de_002": "German - Male", "es_002": "Spanish - Male",
    # Americas
    "es_mx_002": "Spanish MX - Male", "br_001": "Portuguese BR - Female 1",
    "br_003": "Portuguese BR - Female 2", "br_004": "Portuguese BR - Female 3",
    "br_005": "Portuguese BR - Male",
    # Asia
    "id_001": "Indonesian - Female", "jp_001": "Japanese - Female 1",
    "jp_003": "Japanese - Female 2", "jp_005": "Japanese - Female 3",
    "jp_006": "Japanese - Male", "kr_002": "Korean - Male 1",
    "kr_003": "Korean - Female", "kr_004": "Korean - Male 2",
    # Singing
    "en_female_f08_salut_damour": "Singing - Alto",
    "en_male_m03_lobby": "Singing - Tenor",
    "en_female_f08_warmy_breeze": "Singing - Warmy Breeze",
    "en_male_m03_sunshine_soon": "Singing - Sunshine Soon",
    # Other
    "en_male_narration": "Narrator", "en_male_funny": "Wacky",
    "en_female_emotional": "Peaceful",
}
VOICES = list(VOICE_LABELS.keys())
DEFAULT_VOICE = "en_us_006"


class TikTokTTSError(Exception):
    """Raised when none of the TikTok relay endpoints could synthesize audio."""


def list_tiktok_voices():
    """Return the TikTok voices in the dispatcher's voice schema."""
    voices = [
        {"id": vid, "name": label, "category": "tiktok"}
        for vid, label in VOICE_LABELS.items()
    ]
    return {"voices": voices}


def _split_text(text, limit=300):
    """Split text into <= ``limit`` character chunks on punctuation/word boundaries."""
    separated = re.findall(r".*?[.,!?:;-]|.+", text)

    bounded = []
    for chunk in separated:
        if len(chunk) <= limit:
            bounded.append(chunk)
            continue
        current = ""
        for word in chunk.split(" "):
            if len(current) + len(word) + 1 <= limit:
                current = f"{current} {word}".strip()
            else:
                bounded.append(current)
                current = word
        if current:
            bounded.append(current)

    merged, current = [], ""
    for chunk in bounded:
        if len(current) + len(chunk) <= limit:
            current += chunk
        else:
            merged.append(current)
            current = chunk
    merged.append(current)
    return merged


def tts(text, voice, output_filename="output.mp3"):
    """
    Synthesize ``text`` with ``voice`` to an MP3 file via a TikTok relay.

    Raises:
        ValueError: invalid voice or empty text.
        TikTokTTSError: all relay endpoints failed.
    """
    if voice not in VOICES:
        raise ValueError(f"Invalid TikTok voice: {voice}")
    if not text:
        raise ValueError("text must not be empty")

    chunks = _split_text(text)

    for endpoint in ENDPOINT_DATA:
        audio_data = ["" for _ in chunks]
        endpoint_ok = True

        def fetch(index, chunk):
            nonlocal endpoint_ok
            if not endpoint_ok:
                return
            try:
                response = requests.post(
                    endpoint["url"], json={"text": chunk, "voice": voice}, timeout=30
                )
            except requests.RequestException as exc:
                logger.warning("TikTok endpoint %s failed: %s", endpoint["url"], exc)
                endpoint_ok = False
                return
            if response.status_code == 200:
                audio_data[index] = response.json()[endpoint["response"]]
            else:
                endpoint_ok = False

        threads = [Thread(target=fetch, args=(i, c)) for i, c in enumerate(chunks)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        if not endpoint_ok or not all(audio_data):
            continue

        with open(output_filename, "wb") as handle:
            handle.write(base64.b64decode("".join(audio_data)))
        logger.info("TikTok TTS generated %s via %s", output_filename, endpoint["url"])
        return

    raise TikTokTTSError("All TikTok TTS endpoints failed")


def generate_wav_tiktok(text, voice, output_file):
    """
    Synthesize ``text`` to a WAV file using TikTok voices.

    Returns:
        dict: {} on success, {"error": "..."} on failure.
    """
    text = (text or "").strip()
    if not text:
        return {"error": "No text content to process"}
    if not voice or voice == "default":
        voice = DEFAULT_VOICE

    temp_mp3 = "temp_tiktok.mp3"
    try:
        tts(text, voice, temp_mp3)
        from pydub import AudioSegment

        AudioSegment.from_mp3(temp_mp3).export(output_file, format="wav")
        return {}
    except (ValueError, TikTokTTSError) as exc:
        return {"error": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive
        return {"error": f"TikTok synthesis failed: {exc}"}
    finally:
        if os.path.exists(temp_mp3):
            os.remove(temp_mp3)

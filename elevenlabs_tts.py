"""
ElevenLabs Text-to-Speech Implementation
Replaces TikTok TTS functionality with ElevenLabs API
"""

import os
import requests
import validators
from dotenv import load_dotenv
from goose3 import Goose
from cleantext import cleantext

# Load environment variables
load_dotenv()

def get_elevenlabs_voices():
    """
    Get list of available voices from ElevenLabs API using the official client.

    Returns:
        dict: {"voices": [...], "error": "..."}
    """
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        return {"error": "ElevenLabs API key not configured"}

    try:
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=api_key)

        # Get voices using the official client
        voices_response = client.voices.get_all()

        voices = []
        for voice in voices_response.voices:
            voices.append({
                'id': voice.voice_id,
                'name': voice.name,
                'category': voice.category if hasattr(voice, 'category') else 'unknown'
            })

        return {"voices": voices}

    except Exception as e:
        # Fallback to direct API call if client doesn't work
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": api_key
            }

            response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                voices = []
                for voice in data.get('voices', []):
                    voices.append({
                        'id': voice['voice_id'],
                        'name': voice['name'],
                        'category': voice.get('category', 'unknown')
                    })
                return {"voices": voices}
            else:
                return {"error": f"ElevenLabs API error: {response.status_code} - {response.text}"}

        except Exception as fallback_error:
            return {"error": f"Failed to fetch voices: {str(e)} | Fallback error: {str(fallback_error)}"}

def generate_wav_elevenlabs(article, voice_id, output_file):
    """
    Generate a WAV audio file from text using ElevenLabs TTS API.

    Args:
        article (str): Either a URL to an article or direct text content
        voice_id (str): The ElevenLabs voice ID to use for synthesis
        output_file (str): Path where the output WAV file will be saved

    Returns:
        dict: {"error": "error message"} if failed, {} if successful
    """
    try:
        # Check API key
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            return {"error": "ElevenLabs API key not configured. Please set ELEVENLABS_API_KEY environment variable."}

        g = Goose()
        # Check if the input is a URL
        if validators.url(article):
            # If it's a URL, extract text using Goose
            try:
                extracted_article = g.extract(article)
                text = extracted_article.cleaned_text
                if not text or len(text.strip()) == 0:
                    return {"error": "No text content could be extracted from the URL"}
            except Exception as e:
                return {"error": f"Failed to extract text from URL: {str(e)}"}
        else:
            # If it's not a URL, assume it's direct text
            text = cleantext(article)

        # Check text length
        if len(text) == 0:
            return {"error": "No text content to process"}

        # ElevenLabs has a character limit per request (usually around 2500 characters)
        # For longer texts, we'll need to split and concatenate
        max_chunk_size = 2000  # Conservative limit

        if len(text) > max_chunk_size:
            # Split text into chunks
            chunks = []
            words = text.split()
            current_chunk = ""

            for word in words:
                if len(current_chunk + " " + word) <= max_chunk_size:
                    current_chunk += " " + word if current_chunk else word
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = word

            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks = [text.strip()]

        # Generate audio for each chunk
        audio_segments = []

        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            try:
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": api_key
                }

                data = {
                    "text": chunk,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }

                response = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    json=data,
                    headers=headers,
                    timeout=30
                )

                if response.status_code == 200:
                    # Save this chunk as a temporary MP3 file
                    temp_file = f"temp_chunk_{i}.mp3"
                    with open(temp_file, 'wb') as f:
                        f.write(response.content)
                    audio_segments.append(temp_file)
                else:
                    # Clean up any temporary files
                    for temp_file in audio_segments:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    return {"error": f"ElevenLabs API error: {response.status_code} - {response.text}"}

            except Exception as e:
                # Clean up any temporary files
                for temp_file in audio_segments:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                return {"error": f"Text-to-speech generation failed for chunk {i+1}: {str(e)}"}

        if not audio_segments:
            return {"error": "No audio segments were generated"}

        # Combine audio segments if multiple chunks
        try:
            # Handle Python 3.13 audioop removal
            # audioop-lts provides 'audioop' directly
            from pydub import AudioSegment

            if len(audio_segments) == 1:
                # Single segment, just convert to WAV
                sound = AudioSegment.from_mp3(audio_segments[0])
            else:
                # Multiple segments, concatenate them
                combined = AudioSegment.empty()
                for segment_file in audio_segments:
                    segment = AudioSegment.from_mp3(segment_file)
                    combined += segment
                sound = combined

            # Export as WAV
            sound.export(output_file, format="wav")

            # Clean up temporary files
            for temp_file in audio_segments:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

            return {}  # Success

        except Exception as e:
            # Clean up temporary files
            for temp_file in audio_segments:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            return {"error": f"Audio processing failed: {str(e)}"}

    except Exception as e:
        return {"error": f"Unexpected error in generate_wav_elevenlabs: {str(e)}"}

# Mapping of old TikTok voice IDs to ElevenLabs voice IDs (will be updated when voices are fetched)
VOICE_MAPPING = {
    "en_us_006": "default",  # Will be replaced with actual ElevenLabs voice IDs
    "en_us_001": "default",
    "en_us_ghostface": "default",
    "en_us_chewbacca": "default",
    "en_us_c3po": "default",
    "en_us_stitch": "default",
    "en_us_stormtrooper": "default",
    "en_us_rocket": "default",
    "en_au_002": "default",
    "en_au_001": "default",
    "en_uk_001": "default",
    "en_female_emotional": "default",
    "en_female_f08_salut_damour": "default",
    "en_male_m03_lobby": "default"
}

def get_elevenlabs_voice_id(tiktok_voice):
    """
    Convert TikTok voice ID to ElevenLabs voice ID.
    For now, this returns a default voice, but can be expanded to map specific voices.

    Args:
        tiktok_voice (str): Original TikTok voice ID

    Returns:
        str: ElevenLabs voice ID
    """
    # Get the first available voice as default
    voices_result = get_elevenlabs_voices()
    if "voices" in voices_result and len(voices_result["voices"]) > 0:
        return voices_result["voices"][0]["id"]

    # Fallback to a known voice ID (you should replace this with an actual voice ID)
    return "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice
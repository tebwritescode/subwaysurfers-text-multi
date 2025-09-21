# Import ElevenLabs TTS implementation instead of TikTok
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from elevenlabs_tts import generate_wav_elevenlabs, get_elevenlabs_voice_id
import validators

# Pydub should be available since it's in requirements
PYDUB_AVAILABLE = True

def generate_wav(article, voice, output_file):
    """
    Generate a WAV audio file from text or article URL using ElevenLabs text-to-speech.

    This function takes either a direct text input or a URL to an article,
    converts the text to speech using ElevenLabs API, and saves
    the result as a WAV file.

    Args:
        article (str): Either a URL to an article or direct text content
        voice (str): The voice ID to use for text-to-speech synthesis (TikTok format, will be converted)
        output_file (str): Path where the output WAV file will be saved

    Returns:
        dict: {"error": "error message"} if failed, {} if successful

    Note:
        - If article is a valid URL, the function will extract the article text using Goose
        - Voice IDs from TikTok format are converted to ElevenLabs voice IDs
        - The function directly generates WAV format using ElevenLabs API
    """
    try:
        # Convert TikTok voice ID to ElevenLabs voice ID
        elevenlabs_voice_id = get_elevenlabs_voice_id(voice)

        # Use ElevenLabs TTS implementation
        result = generate_wav_elevenlabs(article, elevenlabs_voice_id, output_file)

        return result

    except Exception as e:
        return {"error": f"Unexpected error in generate_wav: {str(e)}"}

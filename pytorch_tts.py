#!/usr/bin/env python3
"""
PyTorch TTS Client Module
Interfaces with the PyTorch TTS server for Bark voice synthesis
"""
import os
import requests
import base64
import time
from pathlib import Path
from typing import Optional

class PyTorchTTSClient:
    """Client for PyTorch TTS Server"""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip('/')

    def health_check(self) -> bool:
        """Check if the server is healthy"""
        try:
            response = requests.get(f"{self.endpoint}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def synthesize(self, text: str, voice: str = "narrator", model: str = "suno/bark") -> Optional[bytes]:
        """Synthesize speech and return audio bytes"""
        try:
            payload = {
                "text": text,
                "voice": voice,
                "model": model,
                "language": "en"
            }

            response = requests.post(
                f"{self.endpoint}/synthesize",
                json=payload,
                timeout=120
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("audio_data"):
                    # Decode base64 audio
                    audio_bytes = base64.b64decode(data["audio_data"])
                    return audio_bytes
            return None
        except Exception as e:
            print(f"PyTorch TTS synthesis error: {e}")
            return None

def tts(text: str, voice: str, output_file: str,
        pytorch_endpoint: Optional[str] = None,
        model: Optional[str] = None) -> bool:
    """
    Generate TTS audio using PyTorch TTS server

    Args:
        text: Text to synthesize
        voice: Voice name or audio file path for cloning
        output_file: Output file path
        pytorch_endpoint: PyTorch TTS server endpoint
        model: Model to use (default: suno/bark)

    Returns:
        True if successful, False otherwise
    """
    if not pytorch_endpoint:
        pytorch_endpoint = os.getenv('PYTORCH_TTS_ENDPOINT', 'http://localhost:8000')

    if not model:
        model = os.getenv('PYTORCH_TTS_MODEL', 'suno/bark')

    client = PyTorchTTSClient(pytorch_endpoint)

    # Map TikTok voices to Bark voices
    voice_mapping = {
        # TikTok to Bark voice mapping
        'en_us_001': 'narrator',
        'en_us_002': 'announcer',
        'en_us_006': 'excited',
        'en_us_007': 'calm',
        'en_us_009': 'deep',
        'en_us_010': 'narrator',
        # Direct Bark voice names
        'narrator': 'narrator',
        'announcer': 'announcer',
        'excited': 'excited',
        'calm': 'calm',
        'deep': 'deep',
        # Additional speaker voices
        'speaker_0': 'speaker_0',
        'speaker_1': 'speaker_1',
        'speaker_2': 'speaker_2',
        'speaker_3': 'speaker_3',
        'speaker_4': 'speaker_4',
        'speaker_5': 'speaker_5',
        'speaker_6': 'speaker_6',
        'speaker_7': 'speaker_7',
        'speaker_8': 'speaker_8',
        'speaker_9': 'speaker_9',
    }

    # Get the Bark voice name
    bark_voice = voice_mapping.get(voice, 'narrator')

    # Handle voice cloning mode (for future enhancement)
    if voice.endswith(('.wav', '.mp3', '.flac')) and os.path.exists(voice):
        print(f"Voice cloning from {voice} not yet implemented, using default narrator")
        bark_voice = 'narrator'

    # Synthesize audio
    audio_bytes = client.synthesize(text, bark_voice, model)

    if audio_bytes:
        # Save audio to file
        try:
            with open(output_file, 'wb') as f:
                f.write(audio_bytes)
            print(f"Generated {output_file} using Bark voice: {bark_voice}")
            return True
        except Exception as e:
            print(f"Error saving audio file: {e}")
            return False
    else:
        print(f"Failed to synthesize audio with PyTorch TTS")
        return False

def get_available_voices(endpoint: Optional[str] = None) -> list:
    """Get list of available voices from the server"""
    if not endpoint:
        endpoint = os.getenv('PYTORCH_TTS_ENDPOINT', 'http://localhost:8000')

    try:
        response = requests.get(f"{endpoint}/voices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('voices', [])
    except:
        pass

    return []
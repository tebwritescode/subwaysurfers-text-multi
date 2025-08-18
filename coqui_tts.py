# Coqui TTS API client for voice generation and cloning
# Supports custom Coqui TTS endpoints with voice cloning capabilities
import requests
import base64
import os
import sys
from threading import Thread
from typing import Optional, Dict, Any

# Optional playsound import (not needed in Docker/server environments)
try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    def playsound(*args, **kwargs):
        pass  # No-op when playsound is not available

class CoquiTTSClient:
    """
    Client for interacting with Coqui TTS API endpoints.
    Supports both standard voices and custom voice cloning.
    """
    
    def __init__(self, endpoint_url: str = "http://localhost:5000"):
        """
        Initialize the Coqui TTS client.
        
        Args:
            endpoint_url (str): Base URL of the Coqui TTS server
        """
        self.endpoint_url = endpoint_url.rstrip('/')
        
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices from the TTS server.
        
        Returns:
            Dict containing available voices or error message
        """
        try:
            response = requests.get(f"{self.endpoint_url}/voices")
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to fetch voices: {response.status_code}"}
        except requests.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def synthesize_speech(self, 
                         text: str, 
                         voice: str = "default",
                         speaker_wav: Optional[str] = None,
                         language: str = "en",
                         output_filename: str = "output.wav") -> Dict[str, Any]:
        """
        Synthesize speech using the Coqui TTS API.
        
        Args:
            text (str): Text to convert to speech
            voice (str): Voice ID to use (for predefined voices)
            speaker_wav (str, optional): Path to speaker reference audio for voice cloning
            language (str): Language code (default: "en")
            output_filename (str): Output audio file path
            
        Returns:
            Dict: Success/error status
        """
        if not text or not text.strip():
            return {"error": "Text cannot be empty"}
            
        # Prepare request payload
        payload = {
            "text": text,
            "language": language
        }
        
        files = {}
        
        # Handle voice cloning with speaker reference
        if speaker_wav and os.path.exists(speaker_wav):
            with open(speaker_wav, 'rb') as f:
                files['speaker_wav'] = f.read()
            payload['use_speaker_reference'] = True
        else:
            payload['voice'] = voice
            
        try:
            # Make request to TTS endpoint
            if files:
                # Use multipart form data for file upload
                response = requests.post(
                    f"{self.endpoint_url}/tts",
                    data=payload,
                    files={'speaker_wav': files['speaker_wav']} if files else None,
                    timeout=60
                )
            else:
                response = requests.post(
                    f"{self.endpoint_url}/tts",
                    json=payload,
                    timeout=60
                )
                
            if response.status_code == 200:
                # Check if response is JSON (error) or binary (audio)
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    # Error response
                    return response.json()
                elif 'audio/' in content_type or 'application/octet-stream' in content_type:
                    # Audio response
                    with open(output_filename, 'wb') as f:
                        f.write(response.content)
                    return {"success": True, "output_file": output_filename}
                else:
                    # Assume base64 encoded audio in JSON
                    try:
                        json_response = response.json()
                        if 'audio' in json_response:
                            audio_data = base64.b64decode(json_response['audio'])
                            with open(output_filename, 'wb') as f:
                                f.write(audio_data)
                            return {"success": True, "output_file": output_filename}
                        else:
                            return {"error": "Unexpected response format"}
                    except:
                        return {"error": "Failed to parse response"}
            else:
                try:
                    error_data = response.json()
                    return {"error": error_data.get("error", f"HTTP {response.status_code}")}
                except:
                    return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
                    
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def clone_voice(self, 
                   text: str, 
                   speaker_wav_path: str,
                   language: str = "en",
                   output_filename: str = "cloned_output.wav") -> Dict[str, Any]:
        """
        Clone a voice using a reference audio file.
        
        Args:
            text (str): Text to synthesize
            speaker_wav_path (str): Path to reference audio file (6+ seconds recommended)
            language (str): Language code
            output_filename (str): Output file path
            
        Returns:
            Dict: Success/error status
        """
        if not os.path.exists(speaker_wav_path):
            return {"error": f"Speaker reference file not found: {speaker_wav_path}"}
            
        return self.synthesize_speech(
            text=text,
            speaker_wav=speaker_wav_path,
            language=language,
            output_filename=output_filename
        )


# Compatibility functions to replace tiktokvoice.py
def tts(text: str, voice: str, output_filename: str = "output.mp3", play_sound: bool = False, 
        coqui_endpoint: str = None, speaker_wav: str = None) -> None:
    """
    Text-to-speech function compatible with existing tiktokvoice.py interface.
    
    Args:
        text (str): Text to convert to speech
        voice (str): Voice identifier or path to speaker reference
        output_filename (str): Output file path
        play_sound (bool): Whether to play the audio after generation
        coqui_endpoint (str): Custom Coqui TTS endpoint URL
        speaker_wav (str): Path to speaker reference for voice cloning
    """
    # Get endpoint from environment or parameter
    endpoint = coqui_endpoint or os.getenv('COQUI_TTS_ENDPOINT', 'http://localhost:5000')
    
    client = CoquiTTSClient(endpoint)
    
    # Determine if we're doing voice cloning or using predefined voice
    if speaker_wav or voice.endswith('.wav') or voice.endswith('.mp3'):
        # Voice cloning mode
        speaker_path = speaker_wav or voice
        result = client.clone_voice(text, speaker_path, output_filename=output_filename)
    else:
        # Standard voice mode
        result = client.synthesize_speech(text, voice, output_filename=output_filename)
    
    if "error" in result:
        raise ValueError(f"TTS generation failed: {result['error']}")
    
    print(f"File '{output_filename}' has been generated successfully.")
    
    if play_sound and PLAYSOUND_AVAILABLE:
        playsound(output_filename)


# Predefined voices for backward compatibility
# These would be managed by your Coqui TTS server
VOICES = [
    'morgan_freeman',       # Custom Morgan Freeman voice
    'default',             # Default voice
    'male_1',              # Male voice option 1
    'female_1',            # Female voice option 1
    'narrator',            # Narrator voice
    # Add more as available on your TTS server
]

def get_voices() -> list:
    """Get list of available voices from the TTS server."""
    endpoint = os.getenv('COQUI_TTS_ENDPOINT', 'http://localhost:5000')
    client = CoquiTTSClient(endpoint)
    voices_data = client.get_available_voices()
    
    if "error" in voices_data:
        print(f"Warning: Could not fetch voices from server: {voices_data['error']}")
        return VOICES  # Return default list
    
    return voices_data.get('voices', VOICES)
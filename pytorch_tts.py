# PyTorch TTS client for external server integration
# Supports Hugging Face models and custom voice selection
import requests
import os
import sys
import tempfile
from typing import Optional, Dict, Any, List

# Optional playsound import (not needed in Docker/server environments)
try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False
    def playsound(*args, **kwargs):
        pass  # No-op when playsound is not available

class PyTorchTTSClient:
    """
    Client for interacting with external PyTorch TTS server.
    Supports Hugging Face models and custom voice selection.
    """
    
    def __init__(self, endpoint_url: str = "http://localhost:8000"):
        """
        Initialize the PyTorch TTS client.
        
        Args:
            endpoint_url (str): Base URL of the PyTorch TTS server
        """
        self.endpoint_url = endpoint_url.rstrip('/')
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """
        Check if the TTS server is available and responding.
        
        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.endpoint_url}/health", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices from the TTS server.
        
        Returns:
            Dict containing available voices or error message
        """
        try:
            response = self.session.get(f"{self.endpoint_url}/voices", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to fetch voices: {response.status_code}"}
        except requests.RequestException as e:
            return {"error": f"Connection error: {str(e)}"}
    
    def synthesize_speech(self, 
                         text: str, 
                         voice: str = "default",
                         model: str = "microsoft/speecht5_tts",
                         language: str = "en",
                         speaker_embedding: Optional[str] = None,
                         output_filename: str = "output.wav") -> Dict[str, Any]:
        """
        Synthesize speech using the PyTorch TTS server.
        
        Args:
            text (str): Text to convert to speech
            voice (str): Voice ID to use
            model (str): Hugging Face model identifier
            language (str): Language code (default: "en")
            speaker_embedding (str, optional): Path to speaker embedding file
            output_filename (str): Output audio file path
            
        Returns:
            Dict: Success/error status
        """
        if not text or not text.strip():
            return {"error": "Text cannot be empty"}
            
        # Prepare request payload
        payload = {
            "text": text,
            "voice": voice,
            "model": model,
            "language": language
        }
        
        files = {}
        
        # Handle speaker embedding file upload
        if speaker_embedding and os.path.exists(speaker_embedding):
            with open(speaker_embedding, 'rb') as f:
                files['speaker_embedding'] = f.read()
            payload['use_speaker_embedding'] = True
            
        try:
            # Make request to TTS endpoint
            if files:
                # Use multipart form data for file upload
                response = self.session.post(
                    f"{self.endpoint_url}/synthesize",
                    data=payload,
                    files={'speaker_embedding': files['speaker_embedding']} if files else None,
                    timeout=120  # Longer timeout for synthesis
                )
            else:
                response = self.session.post(
                    f"{self.endpoint_url}/synthesize",
                    json=payload,
                    timeout=120
                )
                
            if response.status_code == 200:
                # Check content type to determine response format
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    # Check if it's an error or success with base64 audio
                    json_response = response.json()
                    if 'error' in json_response:
                        return json_response
                    elif 'audio_data' in json_response:
                        # Base64 encoded audio
                        import base64
                        audio_data = base64.b64decode(json_response['audio_data'])
                        with open(output_filename, 'wb') as f:
                            f.write(audio_data)
                        return {"success": True, "output_file": output_filename}
                    else:
                        return {"error": "Unexpected JSON response format"}
                        
                elif 'audio/' in content_type or 'application/octet-stream' in content_type:
                    # Direct binary audio response
                    with open(output_filename, 'wb') as f:
                        f.write(response.content)
                    return {"success": True, "output_file": output_filename}
                else:
                    return {"error": f"Unexpected content type: {content_type}"}
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
                   reference_audio: str,
                   model: str = "coqui/XTTS-v2",
                   language: str = "en",
                   output_filename: str = "cloned_output.wav") -> Dict[str, Any]:
        """
        Clone a voice using a reference audio file.
        
        Args:
            text (str): Text to synthesize
            reference_audio (str): Path to reference audio file
            model (str): Hugging Face model for voice cloning
            language (str): Language code
            output_filename (str): Output file path
            
        Returns:
            Dict: Success/error status
        """
        if not os.path.exists(reference_audio):
            return {"error": f"Reference audio file not found: {reference_audio}"}
            
        try:
            with open(reference_audio, 'rb') as f:
                files = {'reference_audio': f}
                data = {
                    'text': text,
                    'model': model,
                    'language': language
                }
                
                response = self.session.post(
                    f"{self.endpoint_url}/clone",
                    data=data,
                    files=files,
                    timeout=180  # Longer timeout for cloning
                )
                
            if response.status_code == 200:
                with open(output_filename, 'wb') as f:
                    f.write(response.content)
                return {"success": True, "output_file": output_filename}
            else:
                try:
                    error_data = response.json()
                    return {"error": error_data.get("error", f"HTTP {response.status_code}")}
                except:
                    return {"error": f"Cloning failed: HTTP {response.status_code}"}
                    
        except requests.RequestException as e:
            return {"error": f"Voice cloning request failed: {str(e)}"}


# Compatibility functions for existing tiktokvoice.py interface
def tts(text: str, voice: str, output_filename: str = "output.mp3", play_sound: bool = False, 
        pytorch_endpoint: str = None, model: str = None, speaker_embedding: str = None) -> None:
    """
    Text-to-speech function compatible with existing tiktokvoice.py interface.
    
    Args:
        text (str): Text to convert to speech
        voice (str): Voice identifier
        output_filename (str): Output file path
        play_sound (bool): Whether to play the audio after generation
        pytorch_endpoint (str): Custom PyTorch TTS endpoint URL
        model (str): Hugging Face model to use
        speaker_embedding (str): Path to speaker embedding file
    """
    # Get endpoint from environment or parameter
    endpoint = pytorch_endpoint or os.getenv('PYTORCH_TTS_ENDPOINT')
    
    if not endpoint:
        raise ValueError("PyTorch TTS endpoint not configured")
    
    client = PyTorchTTSClient(endpoint)
    
    # Use provided model or default
    model = model or os.getenv('PYTORCH_TTS_MODEL', 'microsoft/speecht5_tts')
    
    # Check if we're doing voice cloning (reference audio file)
    if voice.endswith(('.wav', '.mp3', '.flac')) and os.path.exists(voice):
        # Voice cloning mode
        result = client.clone_voice(text, voice, model=model, output_filename=output_filename)
    else:
        # Standard synthesis mode
        result = client.synthesize_speech(
            text, 
            voice, 
            model=model, 
            speaker_embedding=speaker_embedding,
            output_filename=output_filename
        )
    
    if "error" in result:
        raise ValueError(f"TTS generation failed: {result['error']}")
    
    print(f"File '{output_filename}' has been generated successfully.")
    
    if play_sound and PLAYSOUND_AVAILABLE:
        playsound(output_filename)


# Voice mappings for common voices (can be expanded)
VOICE_MAPPINGS = {
    'morgan_freeman': {
        'model': 'drewThomasson/Morgan_freeman_xtts_model',
        'voice': 'morgan_freeman'
    },
    'default': {
        'model': 'microsoft/speecht5_tts', 
        'voice': 'default'
    },
    'parler_mini': {
        'model': 'parler-tts/parler-tts-mini-v1',
        'voice': 'default'
    },
    'melo_english': {
        'model': 'myshell-ai/MeloTTS-English',
        'voice': 'EN-US'
    }
}

def get_voices() -> List[str]:
    """Get list of available voice mappings."""
    endpoint = os.getenv('PYTORCH_TTS_ENDPOINT')
    
    if endpoint:
        try:
            client = PyTorchTTSClient(endpoint)
            voices_data = client.get_available_voices()
            
            if "error" not in voices_data and "voices" in voices_data:
                return voices_data["voices"]
        except:
            pass
    
    # Return default mappings if server unavailable
    return list(VOICE_MAPPINGS.keys())
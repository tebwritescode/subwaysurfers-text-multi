#!/usr/bin/env python3
"""
Mock PyTorch TTS Server for Testing
Simulates Bark TTS without actually loading models
"""
import os
import io
import base64
import time
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import soundfile as sf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Mock PyTorch TTS Server",
    description="Mock Bark TTS for testing without model downloads",
    version="1.0.0"
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "narrator"
    model: str = "suno/bark"
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0

class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    duration: Optional[float] = None

# Mock voice characteristics
VOICE_PARAMS = {
    "narrator": {"frequency": 220, "variation": 0.1, "speed": 1.0},
    "announcer": {"frequency": 200, "variation": 0.05, "speed": 0.95},
    "excited": {"frequency": 280, "variation": 0.2, "speed": 1.1},
    "calm": {"frequency": 180, "variation": 0.03, "speed": 0.9},
    "deep": {"frequency": 120, "variation": 0.02, "speed": 0.85},
}

def generate_mock_audio(text: str, voice: str = "narrator") -> tuple[np.ndarray, int]:
    """Generate mock audio that sounds different for each voice"""
    # Get voice parameters
    params = VOICE_PARAMS.get(voice, VOICE_PARAMS["narrator"])

    # Calculate duration based on text length and voice speed
    words = len(text.split())
    base_duration = words * 0.4  # 0.4 seconds per word
    duration = base_duration / params["speed"]

    # Sample rate
    sample_rate = 22050

    # Generate samples
    num_samples = int(duration * sample_rate)
    t = np.linspace(0, duration, num_samples)

    # Create a complex waveform with voice characteristics
    frequency = params["frequency"]
    variation = params["variation"]

    # Base tone
    signal = np.sin(2 * np.pi * frequency * t)

    # Add harmonics for richness
    signal += 0.3 * np.sin(4 * np.pi * frequency * t)
    signal += 0.1 * np.sin(6 * np.pi * frequency * t)

    # Add variation for naturalness
    variation_signal = np.sin(2 * np.pi * 3 * t) * variation
    signal = signal * (1 + variation_signal)

    # Add envelope for speech-like quality
    envelope = np.ones_like(t)
    # Fade in/out
    fade_samples = int(0.05 * sample_rate)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

    # Apply envelope
    signal = signal * envelope * 0.5  # Scale to reasonable volume

    # Add some noise for realism
    noise = np.random.normal(0, 0.01, num_samples)
    signal = signal + noise

    # Ensure signal is in valid range
    signal = np.clip(signal, -1, 1)

    logger.info(f"Generated mock audio: {duration:.1f}s for voice '{voice}'")

    return signal.astype(np.float32), sample_rate

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pytorch_loaded": True,  # Mock as loaded
        "device": "cpu",
        "mock_mode": True
    }

@app.get("/voices")
async def get_voices():
    """Get available Bark voices"""
    voices = {
        "bark_voices": {
            "narrator": {"name": "Narrator", "description": "Story narrator voice", "language": "en"},
            "announcer": {"name": "Announcer", "description": "Professional announcer voice", "language": "en"},
            "excited": {"name": "Excited", "description": "Energetic and enthusiastic", "language": "en"},
            "calm": {"name": "Calm", "description": "Peaceful and relaxed", "language": "en"},
            "deep": {"name": "Deep", "description": "Deep, authoritative voice", "language": "en"}
        },
        "speaker_voices": {
            f"speaker_{i}": {"name": f"Speaker {i}", "description": f"Bark speaker voice {i}", "language": "en"}
            for i in range(10)
        }
    }

    all_voices = {**voices["bark_voices"], **voices["speaker_voices"]}

    return {
        "voices": list(all_voices.keys()),
        "grouped": voices,
        "details": all_voices,
        "recommended": ["narrator", "announcer", "excited", "calm"]
    }

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Synthesize mock speech from text"""
    try:
        logger.info(f"Mock synthesis request: voice={request.voice}, text_length={len(request.text)}")

        # Simulate processing time
        time.sleep(0.5)

        # Generate mock audio
        audio, sample_rate = generate_mock_audio(request.text, request.voice)

        # Convert to WAV format
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, sample_rate, format='WAV')
        audio_bytes = audio_buffer.getvalue()

        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        return TTSResponse(
            success=True,
            audio_data=audio_b64,
            duration=len(audio) / sample_rate
        )

    except Exception as e:
        logger.error(f"Mock synthesis failed: {str(e)}")
        return TTSResponse(success=False, error=str(e))

@app.post("/synthesize/stream")
async def synthesize_speech_stream(request: TTSRequest):
    """Synthesize mock speech and return as audio stream"""
    try:
        # Generate mock audio
        audio, sample_rate = generate_mock_audio(request.text, request.voice)

        # Convert to audio stream
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, sample_rate, format='WAV')
        audio_buffer.seek(0)

        return StreamingResponse(
            io.BytesIO(audio_buffer.read()),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=speech.wav"}
        )

    except Exception as e:
        logger.error(f"Mock streaming synthesis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-voices")
async def test_voices(voices: List[str] = None):
    """Test multiple mock voices with sample text"""
    test_text = "Welcome to Subway Surfers! This is a test of the voice synthesis system."

    if not voices:
        voices = ["narrator", "announcer", "excited", "calm", "deep"]

    results = {}

    for voice in voices:
        try:
            # Generate mock audio
            audio, sample_rate = generate_mock_audio(test_text, voice)

            # Convert to base64
            audio_buffer = io.BytesIO()
            sf.write(audio_buffer, audio, sample_rate, format='WAV')
            audio_bytes = audio_buffer.getvalue()
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

            results[voice] = {
                "success": True,
                "audio_data": audio_b64,
                "duration": len(audio) / sample_rate,
                "sample_rate": sample_rate
            }

        except Exception as e:
            results[voice] = {
                "success": False,
                "error": str(e)
            }

    return {
        "test_text": test_text,
        "voices_tested": voices,
        "results": results,
        "mock_mode": True
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting Mock PyTorch TTS Server on {host}:{port}")
    logger.info("This is a MOCK server for testing - not using real Bark models")

    uvicorn.run(
        "app_mock:app",
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
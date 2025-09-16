#!/usr/bin/env python3
"""
Minimal PyTorch TTS Server for testing
"""
import os
import io
import base64
import tempfile
import logging
from typing import Optional, Dict
import numpy as np

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PyTorch TTS Server (Minimal)",
    description="Minimal TTS Server for Testing",
    version="1.0.0"
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    model: str = "microsoft/speecht5_tts"
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0

class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[float] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {"status": "healthy", "mode": "minimal"}

@app.get("/voices")
async def get_voices():
    """Get available voices - minimal set for testing"""
    return {
        "voices": ["narrator", "announcer", "excited", "calm", "deep"],
        "details": {
            "narrator": {"name": "Narrator", "description": "Story narrator voice"},
            "announcer": {"name": "Announcer", "description": "Professional announcer voice"},
            "excited": {"name": "Excited", "description": "Energetic voice"},
            "calm": {"name": "Calm", "description": "Relaxed voice"},
            "deep": {"name": "Deep", "description": "Deep voice"}
        }
    }

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech - returns dummy audio for testing"""
    try:
        logger.info(f"Synthesize request: voice={request.voice}, text_length={len(request.text)}")

        # For testing, return a simple sine wave as "audio"
        duration = 2.0  # seconds
        sample_rate = 16000
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # A4 note
        audio = np.sin(2 * np.pi * frequency * t) * 0.3

        # Convert to bytes
        audio_bytes = (audio * 32767).astype(np.int16).tobytes()

        # Encode to base64
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')

        return TTSResponse(
            success=True,
            audio_data=audio_b64,
            duration=duration
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {str(e)}")
        return TTSResponse(success=False, error=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting minimal PyTorch TTS server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
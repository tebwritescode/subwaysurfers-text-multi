#!/usr/bin/env python3
"""
PyTorch TTS Server with Lazy Loading
Delays heavy imports until needed
"""
import os
import io
import base64
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PyTorch TTS Server",
    description="Hugging Face TTS Models API Server with Bark Support",
    version="1.0.0"
)

# Global variables for lazy loading
model_cache = {}
torch = None
device = None
initialized = False

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    model: str = "suno/bark"
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0

class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    duration: Optional[float] = None

def initialize_torch():
    """Lazy load torch and related modules"""
    global torch, device, initialized
    if initialized:
        return

    logger.info("Initializing PyTorch (this may take a moment on first run)...")
    import torch as torch_module
    torch = torch_module
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"PyTorch initialized. Using device: {device}")
    initialized = True

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pytorch_loaded": initialized,
        "device": str(device) if device else "not initialized"
    }

@app.get("/")
async def root():
    return {"message": "PyTorch TTS Server is running", "pytorch_loaded": initialized}

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
    """Synthesize speech from text using Bark"""
    try:
        # Initialize torch if not already done
        if not initialized:
            initialize_torch()

        # Import necessary modules after torch is initialized
        import numpy as np
        import soundfile as sf
        from transformers import AutoProcessor, BarkModel

        # Load Bark model if not cached
        if request.model not in model_cache:
            logger.info(f"Loading Bark model: {request.model}")

            # Set memory optimization flags
            os.environ["SUNO_OFFLOAD_CPU"] = "True"
            if "small" in request.model:
                os.environ["SUNO_USE_SMALL_MODELS"] = "True"

            processor = AutoProcessor.from_pretrained(request.model)
            model = BarkModel.from_pretrained(request.model)

            # Move to device if possible
            if device and str(device) != "cpu":
                try:
                    model = model.to(device)
                except Exception as e:
                    logger.warning(f"Could not move model to {device}: {e}")

            model_cache[request.model] = {
                "processor": processor,
                "model": model
            }
            logger.info(f"Model {request.model} loaded successfully")

        # Get cached model
        processor = model_cache[request.model]["processor"]
        model = model_cache[request.model]["model"]

        # Handle voice presets
        voice_presets = {
            "narrator": "v2/en_speaker_9",
            "announcer": "v2/en_speaker_6",
            "excited": "v2/en_speaker_1",
            "calm": "v2/en_speaker_9",
            "deep": "v2/en_speaker_7",
        }

        # Add numbered speakers
        for i in range(10):
            voice_presets[f"speaker_{i}"] = f"v2/en_speaker_{i}"

        voice_preset = voice_presets.get(request.voice, "v2/en_speaker_9")

        # Process text
        inputs = processor(request.text, voice_preset=voice_preset, return_tensors="pt")

        # Move inputs to device if needed
        if device and str(device) != "cpu":
            inputs = {k: v.to(device) if hasattr(v, 'to') else v for k, v in inputs.items()}

        # Generate audio
        with torch.no_grad():
            speech_values = model.generate(**inputs, do_sample=True, fine_temperature=0.4, coarse_temperature=0.8)

        # Convert to numpy
        audio = speech_values.cpu().numpy().squeeze()
        sample_rate = model.generation_config.sample_rate

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
        logger.error(f"Synthesis failed: {str(e)}")
        return TTSResponse(success=False, error=str(e))

@app.post("/test-voices")
async def test_voices(voices: List[str] = None):
    """Test multiple Bark voices with sample text"""
    test_text = "Welcome to Subway Surfers! This is a test of the voice synthesis system."

    if not voices:
        voices = ["narrator", "announcer", "excited", "calm", "deep"]

    results = {}

    for voice in voices:
        try:
            response = await synthesize_speech(TTSRequest(
                text=test_text,
                voice=voice,
                model="suno/bark"
            ))

            if response.success:
                results[voice] = {
                    "success": True,
                    "duration": response.duration
                }
            else:
                results[voice] = {
                    "success": False,
                    "error": response.error
                }

        except Exception as e:
            results[voice] = {
                "success": False,
                "error": str(e)
            }

    return {
        "test_text": test_text,
        "voices_tested": voices,
        "results": results
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting PyTorch TTS Server on {host}:{port}")
    logger.info("Server will lazy-load PyTorch on first synthesis request")

    uvicorn.run(
        "app_lazy:app",
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
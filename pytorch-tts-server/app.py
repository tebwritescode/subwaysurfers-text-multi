#!/usr/bin/env python3
"""
PyTorch TTS Server
Serves Hugging Face TTS models via REST API
"""
import os
import io
import base64
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

import numpy as np

# Lazy imports for heavy libraries
torch = None
torchaudio = None
sf = None
transformers = None

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
import uvicorn

def lazy_import():
    """Lazy import heavy libraries"""
    global torch, torchaudio, sf, transformers
    if torch is None:
        import torch as _torch
        torch = _torch
    if torchaudio is None:
        import torchaudio as _torchaudio
        torchaudio = _torchaudio
    if sf is None:
        import soundfile as _sf
        sf = _sf
    if transformers is None:
        import transformers as _transformers
        transformers = _transformers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PyTorch TTS Server",
    description="Hugging Face TTS Models API Server",
    version="1.0.0"
)

# Global model cache
model_cache = {}
device = None

def get_device():
    """Get compute device lazily"""
    global device
    if device is None:
        lazy_import()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
    return device

class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    model: str = "microsoft/speecht5_tts"
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0

class TTSResponse(BaseModel):
    success: bool
    audio_data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    duration: Optional[float] = None

# Supported models configuration - Focus on Bark and high-quality models
SUPPORTED_MODELS = {
    "suno/bark": {
        "type": "bark",
        "description": "High-quality with emotions, sound effects",
        "sample_rate": 24000,
        "voices": ["announcer", "narrator", "old_narrator", "speaker_0", "speaker_1", "speaker_2", "speaker_3", "speaker_4", "speaker_5", "speaker_6", "speaker_7", "speaker_8", "speaker_9"]
    },
    "suno/bark-small": {
        "type": "bark_small", 
        "description": "Faster version for lower-end hardware",
        "sample_rate": 24000,
        "voices": ["announcer", "narrator", "speaker_0", "speaker_1", "speaker_2", "speaker_3"]
    },
    "microsoft/speecht5_tts": {
        "type": "speecht5",
        "description": "Fast, general purpose TTS",
        "sample_rate": 16000,
        "processor_class": "SpeechT5Processor",
        "model_class": "SpeechT5ForTextToSpeech",
        "vocoder": "microsoft/speecht5_hifigan"
    }
}

def load_model(model_name: str):
    """Load and cache a TTS model"""
    if model_name in model_cache:
        return model_cache[model_name]

    # Ensure libraries are imported
    lazy_import()
    device = get_device()

    logger.info(f"Loading model: {model_name}")
    
    try:
        if model_name not in SUPPORTED_MODELS:
            # Try generic transformers pipeline
            model_data = {
                "pipeline": transformers.pipeline("text-to-speech", model=model_name, device=device),
                "type": "pipeline"
            }
        else:
            model_config = SUPPORTED_MODELS[model_name]
            model_data = {"type": model_config["type"]}
            
            if model_config["type"] in ["bark", "bark_small"]:
                # Set environment variables for memory optimization
                import os
                if model_config["type"] == "bark_small":
                    os.environ["SUNO_USE_SMALL_MODELS"] = "True"
                
                # Enable CPU offloading for memory efficiency
                if not torch.cuda.is_available() or torch.cuda.get_device_properties(0).total_memory < 8e9:
                    os.environ["SUNO_OFFLOAD_CPU"] = "True"
                
                processor = transformers.AutoProcessor.from_pretrained(model_name)
                model = transformers.BarkModel.from_pretrained(model_name).to(device)
                
                model_data.update({
                    "processor": processor,
                    "model": model
                })
                
            elif model_config["type"] == "speecht5":
                processor = transformers.SpeechT5Processor.from_pretrained(model_name)
                model = transformers.SpeechT5ForTextToSpeech.from_pretrained(model_name).to(device)
                vocoder = transformers.SpeechT5HifiGan.from_pretrained(model_config["vocoder"]).to(device)
                
                model_data.update({
                    "processor": processor,
                    "model": model,
                    "vocoder": vocoder
                })
        
        model_cache[model_name] = model_data
        logger.info(f"Successfully loaded model: {model_name}")
        return model_data
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

def synthesize_speecht5(model_data: Dict, text: str, voice: str = "default") -> np.ndarray:
    """Synthesize speech using SpeechT5 model"""
    lazy_import()
    device = get_device()
    processor = model_data["processor"]
    model = model_data["model"]
    vocoder = model_data["vocoder"]

    inputs = processor(text=text, return_tensors="pt").to(device)
    
    # Load speaker embeddings (you would customize this for different voices)
    speaker_embeddings = torch.randn(1, 512).to(device)  # Default random embedding
    
    with torch.no_grad():
        speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
    
    return speech.cpu().numpy()

def synthesize_vits(model_data: Dict, text: str, language: str = "en") -> np.ndarray:
    """Synthesize speech using VITS model"""
    lazy_import()
    device = get_device()
    model = model_data["model"]
    tokenizer = model_data["tokenizer"]

    inputs = tokenizer(text, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        speech = outputs.waveform.squeeze().cpu().numpy()
    
    return speech

def synthesize_bark(model_data: Dict, text: str, voice: str = "narrator") -> tuple[np.ndarray, int]:
    """Synthesize speech using Bark model"""
    lazy_import()
    device = get_device()
    model = model_data["model"]
    processor = model_data["processor"]
    
    # Handle voice presets
    voice_presets = {
        "announcer": "v2/en_speaker_6",
        "narrator": "v2/en_speaker_9", 
        "old_narrator": "v2/en_speaker_7",
        "speaker_0": "v2/en_speaker_0",
        "speaker_1": "v2/en_speaker_1", 
        "speaker_2": "v2/en_speaker_2",
        "speaker_3": "v2/en_speaker_3",
        "speaker_4": "v2/en_speaker_4",
        "speaker_5": "v2/en_speaker_5",
        "speaker_6": "v2/en_speaker_6",
        "speaker_7": "v2/en_speaker_7",
        "speaker_8": "v2/en_speaker_8",
        "speaker_9": "v2/en_speaker_9",
        # Special effects and emotions
        "excited": "v2/en_speaker_1",  # More energetic speaker
        "calm": "v2/en_speaker_9",     # Calmer voice
        "deep": "v2/en_speaker_7",     # Deeper voice
    }
    
    # Select voice preset
    voice_preset = voice_presets.get(voice, voice_presets["narrator"])
    
    # Add some emotion and personality to text for Bark
    enhanced_text = text
    if "[" not in text:  # Don't modify if already has Bark markup
        if len(text) > 100:  # Longer text gets more natural pauses
            enhanced_text = text.replace(". ", ". [pause] ")
        
        # Add subtle emotion based on content
        if "!" in text or "exciting" in text.lower():
            enhanced_text = f"[excited] {enhanced_text}"
        elif "?" in text:
            enhanced_text = f"[curious] {enhanced_text}"
    
    # Process text
    inputs = processor(enhanced_text, voice_preset=voice_preset, return_tensors="pt").to(device)
    
    with torch.no_grad():
        speech_values = model.generate(**inputs, do_sample=True, fine_temperature=0.4, coarse_temperature=0.8)
    
    # Convert to numpy and get sample rate
    audio = speech_values.cpu().numpy().squeeze()
    sample_rate = model.generation_config.sample_rate
    
    return audio, sample_rate

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "device": str(get_device()) if device else "not_initialized"}

@app.get("/voices")
async def get_voices():
    """Get available voices grouped by model"""
    voices = {
        "bark_voices": {
            "announcer": {"name": "Announcer", "description": "Professional announcer voice", "language": "en"},
            "narrator": {"name": "Narrator", "description": "Story narrator voice", "language": "en"},
            "old_narrator": {"name": "Old Narrator", "description": "Older, wiser narrator", "language": "en"},
            "excited": {"name": "Excited", "description": "Energetic and enthusiastic", "language": "en"},
            "calm": {"name": "Calm", "description": "Peaceful and relaxed", "language": "en"},
            "deep": {"name": "Deep", "description": "Deep, authoritative voice", "language": "en"}
        },
        "speaker_voices": {
            f"speaker_{i}": {"name": f"Speaker {i}", "description": f"Bark speaker voice {i}", "language": "en"}
            for i in range(10)
        }
    }
    
    # Flatten for compatibility
    all_voices = {**voices["bark_voices"], **voices["speaker_voices"]}
    
    return {
        "voices": list(all_voices.keys()), 
        "grouped": voices,
        "details": all_voices,
        "recommended": ["narrator", "announcer", "excited", "calm"]
    }

@app.get("/models")
async def get_models():
    """Get supported models"""
    return {"models": list(SUPPORTED_MODELS.keys()), "details": SUPPORTED_MODELS}

@app.post("/test-voices")
async def test_voices(voices: List[str] = None):
    """Test multiple Bark voices with sample text"""
    test_text = "Welcome to Subway Surfers! This is a test of the voice synthesis system. How does this sound?"
    
    if not voices:
        voices = ["narrator", "announcer", "excited", "calm", "deep"]
    
    results = {}
    
    for voice in voices:
        try:
            # Load Bark model
            model_data = load_model("suno/bark")
            
            # Generate audio
            audio, sample_rate = synthesize_bark(model_data, test_text, voice)
            
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
        "results": results
    }

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech from text"""
    try:
        lazy_import()  # Ensure imports are ready
        # Load model
        model_data = load_model(request.model)
        
        # Synthesize based on model type
        if model_data["type"] in ["bark", "bark_small"]:
            audio, sample_rate = synthesize_bark(model_data, request.text, request.voice)
        elif model_data["type"] == "speecht5":
            audio = synthesize_speecht5(model_data, request.text, request.voice)
            sample_rate = 16000
        elif model_data["type"] == "pipeline":
            # Use transformers pipeline
            result = model_data["pipeline"](request.text)
            audio = result["audio"]
            sample_rate = result["sampling_rate"]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model type: {model_data['type']}")
        
        # Convert to audio bytes
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

@app.post("/synthesize/stream")
async def synthesize_speech_stream(request: TTSRequest):
    """Synthesize speech and return as audio stream"""
    try:
        lazy_import()  # Ensure imports are ready
        model_data = load_model(request.model)
        
        if model_data["type"] == "speecht5":
            audio = synthesize_speecht5(model_data, request.text, request.voice)
            sample_rate = 16000
        elif model_data["type"] == "vits":
            audio = synthesize_vits(model_data, request.text, request.language)
            sample_rate = 22050
        elif model_data["type"] == "pipeline":
            result = model_data["pipeline"](request.text)
            audio = result["audio"]
            sample_rate = result["sampling_rate"]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported model type: {model_data['type']}")
        
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
        logger.error(f"Streaming synthesis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clone")
async def clone_voice(
    text: str = Form(...),
    model: str = Form("coqui/XTTS-v2"),
    language: str = Form("en"),
    reference_audio: UploadFile = File(...)
):
    """Clone voice using reference audio"""
    try:
        # Save reference audio temporarily
        temp_dir = tempfile.mkdtemp()
        ref_path = os.path.join(temp_dir, reference_audio.filename)
        
        with open(ref_path, "wb") as f:
            content = await reference_audio.read()
            f.write(content)
        
        # Load XTTS model for cloning
        model_data = load_model(model)
        
        if model_data["type"] == "xtts":
            audio = synthesize_xtts(model_data, text, ref_path, language)
            sample_rate = 24000
        else:
            raise HTTPException(status_code=400, detail="Voice cloning requires XTTS model")
        
        # Convert to audio stream
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio, sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        # Cleanup
        os.remove(ref_path)
        os.rmdir(temp_dir)
        
        return StreamingResponse(
            io.BytesIO(audio_buffer.read()),
            media_type="audio/wav",
            headers={"Content-Disposition": "attachment; filename=cloned_speech.wav"}
        )
        
    except Exception as e:
        logger.error(f"Voice cloning failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
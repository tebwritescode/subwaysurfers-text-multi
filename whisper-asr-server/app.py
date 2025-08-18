#!/usr/bin/env python3
"""
Whisper ASR Server
Provides local speech-to-text with accurate timestamping
"""
import os
import io
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
import logging

import torch
import whisper
import whisper_timestamped as whisper_ts
from faster_whisper import WhisperModel
import soundfile as sf
import librosa
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Whisper ASR Server",
    description="Local Speech-to-Text with Timestamping",
    version="1.0.0"
)

# Global model cache
model_cache = {}
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {device}")

class TranscribeRequest(BaseModel):
    model: str = "base"
    language: Optional[str] = None
    task: str = "transcribe"  # transcribe or translate
    word_timestamps: bool = True
    temperature: float = 0.0

class TranscribeResponse(BaseModel):
    success: bool
    text: Optional[str] = None
    segments: Optional[List[Dict]] = None
    words: Optional[List[Dict]] = None
    language: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None

# Available models
AVAILABLE_MODELS = {
    "tiny": {"size": "39MB", "speed": "~32x realtime", "accuracy": "good"},
    "base": {"size": "74MB", "speed": "~16x realtime", "accuracy": "better"},
    "small": {"size": "244MB", "speed": "~6x realtime", "accuracy": "good"}, 
    "medium": {"size": "769MB", "speed": "~2x realtime", "accuracy": "very good"},
    "large": {"size": "1550MB", "speed": "1x realtime", "accuracy": "best"},
    "large-v2": {"size": "1550MB", "speed": "1x realtime", "accuracy": "best"},
    "large-v3": {"size": "1550MB", "speed": "1x realtime", "accuracy": "best"}
}

def load_whisper_model(model_name: str = "base", use_faster_whisper: bool = True):
    """Load and cache Whisper model"""
    cache_key = f"{model_name}_{'faster' if use_faster_whisper else 'standard'}"
    
    if cache_key in model_cache:
        return model_cache[cache_key]
    
    logger.info(f"Loading Whisper model: {model_name} ({'faster-whisper' if use_faster_whisper else 'standard'})")
    
    try:
        if use_faster_whisper:
            # Use faster-whisper for better performance
            compute_type = "float16" if device.type == "cuda" else "int8"
            model = WhisperModel(
                model_name, 
                device=device.type,
                compute_type=compute_type
            )
        else:
            # Use standard whisper
            model = whisper.load_model(model_name, device=device)
        
        model_cache[cache_key] = {
            "model": model,
            "type": "faster" if use_faster_whisper else "standard",
            "name": model_name
        }
        
        logger.info(f"Successfully loaded {model_name}")
        return model_cache[cache_key]
        
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

def transcribe_with_timestamps(audio_path: str, model_data: Dict, language: Optional[str] = None) -> Dict:
    """Transcribe audio with word-level timestamps"""
    model = model_data["model"]
    model_type = model_data["type"]
    
    try:
        if model_type == "faster":
            # Use faster-whisper
            segments, info = model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                temperature=0.0
            )
            
            # Convert segments to list and extract data
            segments_list = list(segments)
            
            result = {
                "text": " ".join([segment.text for segment in segments_list]),
                "language": info.language,
                "segments": [],
                "words": []
            }
            
            for segment in segments_list:
                seg_dict = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": []
                }
                
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        word_dict = {
                            "start": word.start,
                            "end": word.end,
                            "word": word.word,
                            "probability": getattr(word, 'probability', 0.0)
                        }
                        seg_dict["words"].append(word_dict)
                        result["words"].append(word_dict)
                
                result["segments"].append(seg_dict)
            
        else:
            # Use whisper_timestamped for standard whisper
            audio = whisper.load_audio(audio_path)
            result = whisper_ts.transcribe(
                model,
                audio,
                language=language,
                remove_empty_words=True,
                word_timestamps=True
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "device": str(device),
        "models_loaded": len(model_cache)
    }

@app.get("/models")
async def get_models():
    """Get available Whisper models"""
    return {
        "models": list(AVAILABLE_MODELS.keys()),
        "details": AVAILABLE_MODELS,
        "recommended": {
            "fast": "tiny",
            "balanced": "base", 
            "quality": "small",
            "best": "large-v3"
        }
    }

@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    model: str = Form("base"),
    language: str = Form(None),
    word_timestamps: bool = Form(True),
    temperature: float = Form(0.0)
):
    """Transcribe audio file with timestamps"""
    
    if model not in AVAILABLE_MODELS:
        raise HTTPException(status_code=400, detail=f"Model {model} not supported")
    
    # Create temporary file
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, f"audio_{audio_file.filename}")
    
    try:
        # Save uploaded file
        with open(temp_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Load model
        model_data = load_whisper_model(model, use_faster_whisper=True)
        
        # Get audio duration
        audio_info = sf.info(temp_path)
        duration = audio_info.duration
        
        # Transcribe with timestamps
        result = transcribe_with_timestamps(temp_path, model_data, language)
        
        return TranscribeResponse(
            success=True,
            text=result.get("text", ""),
            segments=result.get("segments", []),
            words=result.get("words", []),
            language=result.get("language"),
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"Transcription request failed: {str(e)}")
        return TranscribeResponse(
            success=False,
            error=str(e)
        )
    finally:
        # Cleanup
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            os.rmdir(temp_dir)
        except:
            pass

@app.post("/transcribe-url")
async def transcribe_from_url(
    url: str = Form(...),
    model: str = Form("base"),
    language: str = Form(None)
):
    """Transcribe audio from URL"""
    
    try:
        # Download audio from URL
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create temporary file
        temp_dir = tempfile.mkdtemp() 
        temp_path = os.path.join(temp_dir, "audio_from_url.wav")
        
        with open(temp_path, "wb") as f:
            f.write(response.content)
        
        # Load model and transcribe
        model_data = load_whisper_model(model)
        result = transcribe_with_timestamps(temp_path, model_data, language)
        
        # Get duration
        audio_info = sf.info(temp_path)
        duration = audio_info.duration
        
        return TranscribeResponse(
            success=True,
            text=result.get("text", ""),
            segments=result.get("segments", []),
            words=result.get("words", []),
            language=result.get("language"),
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"URL transcription failed: {str(e)}")
        return TranscribeResponse(
            success=False,
            error=str(e)
        )
    finally:
        # Cleanup
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            os.rmdir(temp_dir)
        except:
            pass

@app.get("/status")
async def get_status():
    """Get server status and performance info"""
    return {
        "device": str(device),
        "cuda_available": torch.cuda.is_available(),
        "models_loaded": list(model_cache.keys()),
        "memory_usage": {
            "gpu_memory": torch.cuda.memory_allocated() if torch.cuda.is_available() else 0,
            "gpu_cached": torch.cuda.memory_reserved() if torch.cuda.is_available() else 0
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 9000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
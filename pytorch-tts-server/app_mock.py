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
import threading
try:
    import psutil
except ImportError:
    psutil = None
from pathlib import Path
from typing import Optional, Dict, List, Any
from collections import OrderedDict
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

# Mock cache configuration
CACHE_CONFIG = {
    "max_models": int(os.getenv("MAX_CACHED_MODELS", "3")),
    "memory_threshold_gb": float(os.getenv("MEMORY_THRESHOLD_GB", "12.0")),
    "cache_warmup_enabled": os.getenv("CACHE_WARMUP_ENABLED", "true").lower() == "true",
    "warmup_models": os.getenv("WARMUP_MODELS", "suno/bark-small,suno/bark").split(","),
}

class MockModelCache:
    """Mock model cache that simulates the production cache behavior"""
    def __init__(self):
        self._cache = OrderedDict()
        self._access_times = {}
        self._model_sizes = {}
        self._lock = threading.RLock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_cleanups": 0,
            "total_loads": 0
        }
        logger.info(f"Initialized MockModelCache with max_models={CACHE_CONFIG['max_models']}")

    def get(self, model_name: str) -> Optional[Dict]:
        """Get model from mock cache"""
        with self._lock:
            if model_name in self._cache:
                # Move to end (most recently used)
                model_data = self._cache.pop(model_name)
                self._cache[model_name] = model_data
                self._access_times[model_name] = time.time()
                self._stats["hits"] += 1
                logger.debug(f"Mock cache hit for model: {model_name}")
                return model_data

            self._stats["misses"] += 1
            logger.debug(f"Mock cache miss for model: {model_name}")
            return None

    def put(self, model_name: str, model_data: Dict, size_bytes: int = 0):
        """Put model in mock cache"""
        with self._lock:
            # Remove if already exists
            if model_name in self._cache:
                del self._cache[model_name]
                if model_name in self._model_sizes:
                    del self._model_sizes[model_name]

            # Check if we need to evict models
            while len(self._cache) >= CACHE_CONFIG["max_models"]:
                self._evict_lru()

            # Add new model
            self._cache[model_name] = model_data
            self._access_times[model_name] = time.time()
            self._model_sizes[model_name] = size_bytes
            self._stats["total_loads"] += 1

            logger.info(f"Mock cached model: {model_name} (size: {size_bytes / 1024 / 1024:.1f}MB, total cached: {len(self._cache)})")

    def _evict_lru(self):
        """Evict least recently used model"""
        if not self._cache:
            return

        # Get LRU model (first in OrderedDict)
        lru_model = next(iter(self._cache))
        self._cache.pop(lru_model)

        # Remove tracking data
        if lru_model in self._access_times:
            del self._access_times[lru_model]
        if lru_model in self._model_sizes:
            del self._model_sizes[lru_model]

        self._stats["evictions"] += 1
        logger.info(f"Mock evicted LRU model: {lru_model}")

    def clear(self):
        """Clear entire mock cache"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            self._model_sizes.clear()
            logger.info("Mock cache cleared")

    def get_stats(self) -> Dict:
        """Get mock cache statistics"""
        with self._lock:
            cache_memory_mb = sum(self._model_sizes.values()) / (1024 * 1024)

            stats = {
                "cached_models": list(self._cache.keys()),
                "cache_size": len(self._cache),
                "max_cache_size": CACHE_CONFIG["max_models"],
                "cache_memory_mb": round(cache_memory_mb, 1),
                "memory_threshold_gb": CACHE_CONFIG["memory_threshold_gb"],
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": self._stats["hits"] / max(1, self._stats["hits"] + self._stats["misses"]),
                "evictions": self._stats["evictions"],
                "memory_cleanups": self._stats["memory_cleanups"],
                "total_loads": self._stats["total_loads"]
            }

            # Add mock system memory info if psutil is available
            if psutil is not None:
                try:
                    memory_info = psutil.virtual_memory()
                    stats["system_memory_gb"] = round(memory_info.used / (1024**3), 1)
                    stats["system_memory_total_gb"] = round(memory_info.total / (1024**3), 1)
                    stats["system_memory_percent"] = memory_info.percent
                except Exception:
                    stats["system_memory_gb"] = "mock_unavailable"
            else:
                stats["system_memory_gb"] = "mock_psutil_not_available"

            return stats

    def warmup(self, model_names: List[str]):
        """Mock warmup process"""
        def warmup_worker():
            for model_name in model_names:
                try:
                    logger.info(f"Mock warming up model: {model_name}")
                    # Simulate model loading
                    time.sleep(0.1)  # Brief simulation
                    mock_model_data = {
                        "type": "bark" if "bark" in model_name else "mock",
                        "mock": True
                    }
                    # Simulate different sizes for different models
                    if "bark" in model_name and "small" not in model_name:
                        size_bytes = 6 * 1024**3  # 6GB for full Bark
                    elif "bark-small" in model_name:
                        size_bytes = 2 * 1024**3  # 2GB for Bark-small
                    else:
                        size_bytes = 500 * 1024**2  # 500MB default

                    self.put(model_name, mock_model_data, size_bytes)
                except Exception as e:
                    logger.error(f"Failed to mock warm up model {model_name}: {e}")
            logger.info("Mock cache warmup completed")

        if CACHE_CONFIG["cache_warmup_enabled"]:
            warmup_task = threading.Thread(target=warmup_worker, daemon=True)
            warmup_task.start()
            logger.info(f"Started mock cache warmup for models: {model_names}")
        else:
            logger.info("Mock cache warmup disabled")

# Initialize mock cache
mock_cache = MockModelCache()

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

@app.on_event("startup")
async def startup_event():
    """Initialize mock cache and start warmup on server startup"""
    logger.info("Starting Mock PyTorch TTS Server...")

    # Start mock cache warmup
    if CACHE_CONFIG["cache_warmup_enabled"]:
        warmup_models = [model.strip() for model in CACHE_CONFIG["warmup_models"] if model.strip()]
        if warmup_models:
            mock_cache.warmup(warmup_models)

    logger.info("Mock server startup completed")

@app.get("/health")
async def health_check():
    """Health check endpoint with mock cache status"""
    try:
        cache_stats = mock_cache.get_stats()

        return {
            "status": "healthy",
            "device": "cpu",
            "cache": {
                "cached_models": len(cache_stats["cached_models"]),
                "cache_memory_mb": cache_stats["cache_memory_mb"],
                "system_memory_gb": cache_stats["system_memory_gb"],
                "hit_rate": round(cache_stats["hit_rate"], 3)
            },
            "pytorch_loaded": True,  # Mock as loaded
            "mock_mode": True,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Mock health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "mock_mode": True}

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

@app.get("/models")
async def get_models():
    """Get supported models with mock cache status"""
    # Mock supported models
    SUPPORTED_MODELS = {
        "suno/bark": {
            "type": "bark",
            "description": "High-quality with emotions, sound effects (MOCK)",
            "sample_rate": 24000
        },
        "suno/bark-small": {
            "type": "bark_small",
            "description": "Faster version for lower-end hardware (MOCK)",
            "sample_rate": 24000
        },
        "microsoft/speecht5_tts": {
            "type": "speecht5",
            "description": "Fast, general purpose TTS (MOCK)",
            "sample_rate": 16000
        }
    }

    cache_stats = mock_cache.get_stats()
    cached_models = cache_stats["cached_models"]

    models_info = {}
    for model_name, config in SUPPORTED_MODELS.items():
        models_info[model_name] = {
            **config,
            "cached": model_name in cached_models,
            "mock": True
        }

    return {
        "models": list(SUPPORTED_MODELS.keys()),
        "details": models_info,
        "cache_status": {
            "cached_models": cached_models,
            "cache_size": cache_stats["cache_size"],
            "max_cache_size": cache_stats["max_cache_size"]
        },
        "mock_mode": True
    }

@app.get("/cache/stats")
async def get_cache_stats():
    """Get detailed mock cache statistics"""
    stats = mock_cache.get_stats()
    stats["mock_mode"] = True
    return stats

@app.post("/cache/clear")
async def clear_cache():
    """Clear mock cache"""
    try:
        stats_before = mock_cache.get_stats()
        mock_cache.clear()
        stats_after = mock_cache.get_stats()

        return {
            "success": True,
            "message": "Mock cache cleared successfully",
            "freed_memory_mb": stats_before["cache_memory_mb"],
            "models_cleared": stats_before["cached_models"],
            "mock_mode": True
        }
    except Exception as e:
        logger.error(f"Failed to clear mock cache: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to clear mock cache: {str(e)}")

@app.post("/cache/warmup")
async def warmup_cache(models: List[str] = None):
    """Manually trigger mock cache warmup for specific models"""
    try:
        if models is None:
            models = [model.strip() for model in CACHE_CONFIG["warmup_models"] if model.strip()]

        if not models:
            return {"success": False, "message": "No models specified for warmup", "mock_mode": True}

        # Start mock warmup in background
        mock_cache.warmup(models)

        return {
            "success": True,
            "message": f"Mock cache warmup started for {len(models)} models",
            "models": models,
            "mock_mode": True
        }
    except Exception as e:
        logger.error(f"Failed to start mock cache warmup: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to start mock cache warmup: {str(e)}")

@app.post("/cache/preload/{model_name}")
async def preload_model(model_name: str):
    """Preload a specific model into mock cache"""
    try:
        logger.info(f"Mock preloading model: {model_name}")
        start_time = time.time()

        # Simulate model loading
        time.sleep(0.2)  # Brief simulation
        mock_model_data = {
            "type": "bark" if "bark" in model_name else "mock",
            "mock": True
        }
        # Simulate different sizes
        if "bark" in model_name and "small" not in model_name:
            size_bytes = 6 * 1024**3  # 6GB for full Bark
        elif "bark-small" in model_name:
            size_bytes = 2 * 1024**3  # 2GB for Bark-small
        else:
            size_bytes = 500 * 1024**2  # 500MB default

        mock_cache.put(model_name, mock_model_data, size_bytes)

        load_time = time.time() - start_time
        cache_stats = mock_cache.get_stats()

        return {
            "success": True,
            "message": f"Mock model {model_name} preloaded successfully",
            "load_time_seconds": round(load_time, 2),
            "cache_status": {
                "cached_models": cache_stats["cached_models"],
                "cache_memory_mb": cache_stats["cache_memory_mb"]
            },
            "mock_mode": True
        }
    except Exception as e:
        logger.error(f"Failed to mock preload model {model_name}: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to mock preload model: {str(e)}")

@app.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """Synthesize mock speech from text with cache simulation"""
    try:
        logger.info(f"Mock synthesis request: model={request.model}, voice={request.voice}, text_length={len(request.text)}")

        # Simulate cache lookup
        cached_model = mock_cache.get(request.model)
        if cached_model is None:
            # Simulate model loading
            logger.info(f"Mock loading model: {request.model}")
            time.sleep(0.3)  # Simulate loading time

            mock_model_data = {
                "type": "bark" if "bark" in request.model else "mock",
                "mock": True
            }
            # Simulate different sizes
            if "bark" in request.model and "small" not in request.model:
                size_bytes = 6 * 1024**3  # 6GB for full Bark
            elif "bark-small" in request.model:
                size_bytes = 2 * 1024**3  # 2GB for Bark-small
            else:
                size_bytes = 500 * 1024**2  # 500MB default

            mock_cache.put(request.model, mock_model_data, size_bytes)
        else:
            logger.info(f"Mock cache hit for model: {request.model}")

        # Simulate processing time (faster for cached models)
        processing_time = 0.3 if cached_model is None else 0.1
        time.sleep(processing_time)

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
    logger.info(f"Mock cache config: max_models={CACHE_CONFIG['max_models']}, memory_threshold={CACHE_CONFIG['memory_threshold_gb']}GB")
    logger.info(f"Mock cache warmup: {'enabled' if CACHE_CONFIG['cache_warmup_enabled'] else 'disabled'}")

    uvicorn.run(
        "app_mock:app",
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
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
import threading
import time
import gc
try:
    import psutil
except ImportError:
    psutil = None
    logger.warning("psutil not available - memory monitoring disabled")
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from functools import lru_cache
from collections import OrderedDict
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

# Global variables
device = None

# Cache configuration
CACHE_CONFIG = {
    "max_models": int(os.getenv("MAX_CACHED_MODELS", "3")),  # Maximum models in memory
    "memory_threshold_gb": float(os.getenv("MEMORY_THRESHOLD_GB", "12.0")),  # Memory threshold for cleanup
    "cache_warmup_enabled": os.getenv("CACHE_WARMUP_ENABLED", "true").lower() == "true",
    "warmup_models": os.getenv("WARMUP_MODELS", "suno/bark-small,suno/bark").split(","),
    "gc_interval_seconds": int(os.getenv("GC_INTERVAL_SECONDS", "300")),  # 5 minutes
    "memory_check_interval": int(os.getenv("MEMORY_CHECK_INTERVAL", "60"))  # 1 minute
}

class ModelCache:
    """Thread-safe singleton model cache with LRU eviction and memory management"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._cache = OrderedDict()  # LRU cache
        self._access_times = {}  # Track access times
        self._model_sizes = {}  # Track model memory usage
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._warmup_task = None
        self._gc_task = None
        self._memory_monitor_task = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_cleanups": 0,
            "total_loads": 0
        }
        self._initialized = True

        # Start background tasks
        self._start_background_tasks()

        logger.info(f"Initialized ModelCache with max_models={CACHE_CONFIG['max_models']}, memory_threshold={CACHE_CONFIG['memory_threshold_gb']}GB")

    def _start_background_tasks(self):
        """Start background tasks for cache management"""
        # Garbage collection task
        def gc_worker():
            while True:
                time.sleep(CACHE_CONFIG["gc_interval_seconds"])
                self._force_gc()

        # Memory monitoring task
        def memory_monitor():
            while True:
                time.sleep(CACHE_CONFIG["memory_check_interval"])
                self._check_memory_pressure()

        self._gc_task = threading.Thread(target=gc_worker, daemon=True)
        self._memory_monitor_task = threading.Thread(target=memory_monitor, daemon=True)

        self._gc_task.start()
        self._memory_monitor_task.start()

        logger.info("Started background cache management tasks")

    def get(self, model_name: str) -> Optional[Dict]:
        """Get model from cache with LRU update"""
        with self._lock:
            if model_name in self._cache:
                # Move to end (most recently used)
                model_data = self._cache.pop(model_name)
                self._cache[model_name] = model_data
                self._access_times[model_name] = time.time()
                self._stats["hits"] += 1
                logger.debug(f"Cache hit for model: {model_name}")
                return model_data

            self._stats["misses"] += 1
            logger.debug(f"Cache miss for model: {model_name}")
            return None

    def put(self, model_name: str, model_data: Dict, size_bytes: int = 0):
        """Put model in cache with size tracking and LRU eviction"""
        with self._lock:
            # Remove if already exists (for updates)
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

            logger.info(f"Cached model: {model_name} (size: {size_bytes / 1024 / 1024:.1f}MB, total cached: {len(self._cache)})")

    def _evict_lru(self):
        """Evict least recently used model"""
        if not self._cache:
            return

        # Get LRU model (first in OrderedDict)
        lru_model = next(iter(self._cache))
        model_data = self._cache.pop(lru_model)

        # Cleanup model resources
        self._cleanup_model(model_data)

        # Remove tracking data
        if lru_model in self._access_times:
            del self._access_times[lru_model]
        if lru_model in self._model_sizes:
            del self._model_sizes[lru_model]

        self._stats["evictions"] += 1
        logger.info(f"Evicted LRU model: {lru_model}")

    def _cleanup_model(self, model_data: Dict):
        """Cleanup model resources"""
        try:
            # Move models to CPU to free GPU memory
            if "model" in model_data and hasattr(model_data["model"], "to"):
                model_data["model"].to("cpu")
            if "vocoder" in model_data and hasattr(model_data["vocoder"], "to"):
                model_data["vocoder"].to("cpu")

            # Clear CUDA cache if available
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()

        except Exception as e:
            logger.warning(f"Error during model cleanup: {e}")

    def _check_memory_pressure(self):
        """Check system memory and cleanup if necessary"""
        if psutil is None:
            return  # Skip if psutil not available

        try:
            memory_gb = psutil.virtual_memory().used / (1024**3)
            if memory_gb > CACHE_CONFIG["memory_threshold_gb"]:
                logger.warning(f"Memory pressure detected: {memory_gb:.1f}GB > {CACHE_CONFIG['memory_threshold_gb']}GB")
                self._emergency_cleanup()
        except Exception as e:
            logger.error(f"Error checking memory pressure: {e}")

    def _emergency_cleanup(self):
        """Emergency memory cleanup - evict half the cache"""
        with self._lock:
            models_to_evict = len(self._cache) // 2
            for _ in range(models_to_evict):
                if self._cache:
                    self._evict_lru()

            self._force_gc()
            self._stats["memory_cleanups"] += 1
            logger.info(f"Emergency cleanup completed, evicted {models_to_evict} models")

    def _force_gc(self):
        """Force garbage collection and CUDA cache cleanup"""
        try:
            gc.collect()
            if torch and torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.debug("Performed garbage collection")
        except Exception as e:
            logger.warning(f"Error during garbage collection: {e}")

    def clear(self):
        """Clear entire cache"""
        with self._lock:
            # Cleanup all models
            for model_data in self._cache.values():
                self._cleanup_model(model_data)

            self._cache.clear()
            self._access_times.clear()
            self._model_sizes.clear()
            self._force_gc()

            logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
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

            # Add system memory info if psutil is available
            if psutil is not None:
                try:
                    memory_info = psutil.virtual_memory()
                    stats["system_memory_gb"] = round(memory_info.used / (1024**3), 1)
                    stats["system_memory_total_gb"] = round(memory_info.total / (1024**3), 1)
                    stats["system_memory_percent"] = memory_info.percent
                except Exception as e:
                    logger.warning(f"Could not get system memory info: {e}")
                    stats["system_memory_gb"] = "unavailable"
            else:
                stats["system_memory_gb"] = "psutil_not_available"

            return stats

    def warmup(self, model_names: List[str]):
        """Warm up cache with specified models"""
        def warmup_worker():
            for model_name in model_names:
                try:
                    logger.info(f"Warming up model: {model_name}")
                    load_model(model_name)  # This will cache the model
                    time.sleep(1)  # Brief pause between models
                except Exception as e:
                    logger.error(f"Failed to warm up model {model_name}: {e}")
            logger.info("Cache warmup completed")

        if CACHE_CONFIG["cache_warmup_enabled"]:
            self._warmup_task = threading.Thread(target=warmup_worker, daemon=True)
            self._warmup_task.start()
            logger.info(f"Started cache warmup for models: {model_names}")
        else:
            logger.info("Cache warmup disabled")

# Initialize singleton cache instance
model_cache = ModelCache()

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

def estimate_model_size(model_data: Dict) -> int:
    """Estimate model memory usage in bytes"""
    total_bytes = 0
    try:
        for key, obj in model_data.items():
            if hasattr(obj, 'parameters'):
                # PyTorch model
                for param in obj.parameters():
                    total_bytes += param.element_size() * param.nelement()
            elif hasattr(obj, '__sizeof__'):
                total_bytes += obj.__sizeof__()
    except Exception as e:
        logger.warning(f"Could not estimate model size: {e}")
        # Fallback estimates based on model type
        model_type = model_data.get("type", "unknown")
        if "bark" in model_type:
            total_bytes = 6 * 1024**3  # 6GB estimate for Bark
        elif "speecht5" in model_type:
            total_bytes = 1 * 1024**3  # 1GB estimate for SpeechT5
        else:
            total_bytes = 500 * 1024**2  # 500MB default

    return total_bytes

def load_model(model_name: str):
    """Load and cache a TTS model with optimized caching"""
    # Check cache first
    cached_model = model_cache.get(model_name)
    if cached_model is not None:
        return cached_model

    # Ensure libraries are imported
    lazy_import()
    device = get_device()

    logger.info(f"Loading model: {model_name}")
    load_start_time = time.time()

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

        # Estimate model size and cache it
        model_size = estimate_model_size(model_data)
        model_cache.put(model_name, model_data, model_size)

        load_time = time.time() - load_start_time
        logger.info(f"Successfully loaded model: {model_name} in {load_time:.1f}s (size: {model_size / 1024 / 1024:.1f}MB)")
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

@app.on_event("startup")
async def startup_event():
    """Initialize cache and start warmup on server startup"""
    logger.info("Starting PyTorch TTS Server...")

    # Initialize device
    get_device()

    # Start cache warmup
    if CACHE_CONFIG["cache_warmup_enabled"]:
        warmup_models = [model.strip() for model in CACHE_CONFIG["warmup_models"] if model.strip()]
        if warmup_models:
            model_cache.warmup(warmup_models)

    logger.info("Server startup completed")

@app.get("/health")
async def health_check():
    """Health check endpoint with cache status"""
    try:
        device_info = str(get_device()) if device else "not_initialized"
        cache_stats = model_cache.get_stats()

        return {
            "status": "healthy",
            "device": device_info,
            "cache": {
                "cached_models": len(cache_stats["cached_models"]),
                "cache_memory_mb": cache_stats["cache_memory_mb"],
                "system_memory_gb": cache_stats["system_memory_gb"],
                "hit_rate": round(cache_stats["hit_rate"], 3)
            },
            "pytorch_loaded": torch is not None,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

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
    """Get supported models with cache status"""
    cache_stats = model_cache.get_stats()
    cached_models = cache_stats["cached_models"]

    models_info = {}
    for model_name, config in SUPPORTED_MODELS.items():
        models_info[model_name] = {
            **config,
            "cached": model_name in cached_models
        }

    return {
        "models": list(SUPPORTED_MODELS.keys()),
        "details": models_info,
        "cache_status": {
            "cached_models": cached_models,
            "cache_size": cache_stats["cache_size"],
            "max_cache_size": cache_stats["max_cache_size"]
        }
    }

@app.get("/cache/stats")
async def get_cache_stats():
    """Get detailed cache statistics"""
    return model_cache.get_stats()

@app.post("/cache/clear")
async def clear_cache():
    """Clear model cache"""
    try:
        stats_before = model_cache.get_stats()
        model_cache.clear()
        stats_after = model_cache.get_stats()

        return {
            "success": True,
            "message": "Cache cleared successfully",
            "freed_memory_mb": stats_before["cache_memory_mb"],
            "models_cleared": stats_before["cached_models"]
        }
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.post("/cache/warmup")
async def warmup_cache(models: List[str] = None):
    """Manually trigger cache warmup for specific models"""
    try:
        if models is None:
            models = [model.strip() for model in CACHE_CONFIG["warmup_models"] if model.strip()]

        if not models:
            return {"success": False, "message": "No models specified for warmup"}

        # Start warmup in background
        model_cache.warmup(models)

        return {
            "success": True,
            "message": f"Cache warmup started for {len(models)} models",
            "models": models
        }
    except Exception as e:
        logger.error(f"Failed to start cache warmup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start cache warmup: {str(e)}")

@app.post("/cache/preload/{model_name}")
async def preload_model(model_name: str):
    """Preload a specific model into cache"""
    try:
        logger.info(f"Preloading model: {model_name}")
        start_time = time.time()

        # Load model (this will cache it)
        load_model(model_name)

        load_time = time.time() - start_time
        cache_stats = model_cache.get_stats()

        return {
            "success": True,
            "message": f"Model {model_name} preloaded successfully",
            "load_time_seconds": round(load_time, 2),
            "cache_status": {
                "cached_models": cache_stats["cached_models"],
                "cache_memory_mb": cache_stats["cache_memory_mb"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to preload model {model_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preload model: {str(e)}")

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

    logger.info(f"Starting PyTorch TTS Server on {host}:{port}")
    logger.info(f"Cache config: max_models={CACHE_CONFIG['max_models']}, memory_threshold={CACHE_CONFIG['memory_threshold_gb']}GB")
    logger.info(f"Cache warmup: {'enabled' if CACHE_CONFIG['cache_warmup_enabled'] else 'disabled'}")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=False,
        workers=1,
        log_level="info"
    )
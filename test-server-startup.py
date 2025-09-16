#!/usr/bin/env python3
"""Test PyTorch TTS server startup"""
import sys
import os

# Add pytorch-tts-server to path
sys.path.insert(0, '/Users/timbruening/Documents/Projects/claude-code/subwaysurfers-text-multi/pytorch-tts-server')

print("Testing PyTorch TTS server startup...")

# Test imports
try:
    print("1. Testing basic imports...")
    import torch
    import torchaudio
    print(f"   - PyTorch version: {torch.__version__}")
    print(f"   - Device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")

    print("2. Testing FastAPI imports...")
    from fastapi import FastAPI
    import uvicorn
    print("   - FastAPI imported successfully")

    print("3. Testing Transformers imports...")
    from transformers import AutoProcessor, BarkModel
    print("   - Transformers imported successfully")

    print("4. Creating minimal FastAPI app...")
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    print("5. Starting server (press Ctrl+C to stop)...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

except ImportError as e:
    print(f"ERROR: Import failed - {e}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
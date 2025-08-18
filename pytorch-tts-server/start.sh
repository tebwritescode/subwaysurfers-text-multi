#!/bin/bash
# PyTorch TTS Server startup script

set -e

echo "Starting PyTorch TTS Server..."
echo "Device: $(python -c 'import torch; print("CUDA" if torch.cuda.is_available() else "CPU")')"
echo "Port: ${PORT:-8000}"

# Pre-download common models if specified
if [ ! -z "$PRELOAD_MODELS" ]; then
    echo "Pre-loading models: $PRELOAD_MODELS"
    python -c "
import os
from transformers import pipeline
models = os.getenv('PRELOAD_MODELS', '').split(',')
for model in models:
    if model.strip():
        print(f'Loading {model.strip()}...')
        try:
            pipeline('text-to-speech', model=model.strip())
            print(f'Successfully loaded {model.strip()}')
        except Exception as e:
            print(f'Failed to load {model.strip()}: {e}')
"
fi

# Start the server
exec python app.py
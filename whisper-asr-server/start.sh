#!/bin/bash
# Whisper ASR Server startup script

set -e

echo "Starting Whisper ASR Server..."
echo "Device: $(python -c 'import torch; print("CUDA" if torch.cuda.is_available() else "CPU")')"
echo "Port: ${PORT:-9000}"

# Pre-download model if specified
if [ ! -z "$PRELOAD_MODEL" ]; then
    echo "Pre-loading model: $PRELOAD_MODEL"
    python -c "
import whisper
model_name = '${PRELOAD_MODEL}'
print(f'Loading {model_name}...')
try:
    whisper.load_model(model_name)
    print(f'Successfully loaded {model_name}')
except Exception as e:
    print(f'Failed to load {model_name}: {e}')
"
fi

# Start the server
exec python app.py
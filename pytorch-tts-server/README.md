# PyTorch TTS Server

A Docker container that serves Hugging Face TTS models via REST API. Supports voice synthesis, voice cloning, and custom model loading.

## Features

- 🎤 **Multiple TTS Models**: SpeechT5, VITS, XTTS-v2, Bark, and more
- 🔄 **Voice Cloning**: Clone voices using reference audio files  
- 🚀 **High Performance**: GPU acceleration support
- 📦 **Easy Deployment**: Docker container with auto-scaling
- 🎯 **REST API**: Simple HTTP endpoints for integration
- 💾 **Model Caching**: Intelligent model loading and caching

## Supported Models

| Model | Type | Features | Use Case |
|-------|------|----------|----------|
| `microsoft/speecht5_tts` | SpeechT5 | Multi-speaker, fast | General purpose |
| `facebook/mms-tts-eng` | VITS | High quality | English synthesis |
| `coqui/XTTS-v2` | XTTS | Voice cloning | Custom voices |
| `suno/bark` | Bark | Emotional speech | Character voices |
| `drewThomasson/Morgan_freeman_xtts_model` | XTTS | Celebrity voice | Morgan Freeman |

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone and start
git clone <repo>
cd pytorch-tts-server
docker-compose up -d

# Check status
curl http://localhost:8000/health
```

### Using Docker Run

```bash
# CPU version
docker run -p 8000:8000 pytorch-tts-server

# GPU version (requires nvidia-docker)
docker run --gpus all -p 8000:8000 pytorch-tts-server
```

### Build from Source

```bash
# Build container
docker build -t pytorch-tts-server .

# Run with model pre-loading
docker run -p 8000:8000 \
  -e PRELOAD_MODELS="microsoft/speecht5_tts,coqui/XTTS-v2" \
  pytorch-tts-server
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Available Voices
```bash
curl http://localhost:8000/voices
```

### Synthesize Speech (JSON Response)
```bash
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the PyTorch TTS server.",
    "voice": "default",
    "model": "microsoft/speecht5_tts",
    "language": "en"
  }'
```

### Synthesize Speech (Audio Stream)
```bash
curl -X POST http://localhost:8000/synthesize/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "model": "microsoft/speecht5_tts"
  }' \
  --output speech.wav
```

### Voice Cloning
```bash
curl -X POST http://localhost:8000/clone \
  -F "text=Hello, this is my cloned voice!" \
  -F "model=coqui/XTTS-v2" \
  -F "language=en" \
  -F "reference_audio=@path/to/speaker_sample.wav" \
  --output cloned_speech.wav
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `PRELOAD_MODELS` | | Comma-separated list of models to pre-load |
| `CUDA_VISIBLE_DEVICES` | | GPU device selection |

## Integration with Subway Surfers App

Add these environment variables to your main app:

```bash
# Enable PyTorch TTS
export PYTORCH_TTS_ENDPOINT=http://localhost:8000
export PYTORCH_TTS_MODEL=microsoft/speecht5_tts

# For Morgan Freeman voice
export PYTORCH_TTS_MODEL=drewThomasson/Morgan_freeman_xtts_model

# Run your app
docker run -p 5000:5000 \
  -e PYTORCH_TTS_ENDPOINT=http://pytorch-tts-server:8000 \
  -e PYTORCH_TTS_MODEL=drewThomasson/Morgan_freeman_xtts_model \
  --link pytorch-tts-server \
  tebwritescode/subwaysurfers-text20:latest
```

## Performance Notes

- **CPU**: Works on any system, ~5-10x slower than GPU
- **GPU**: Requires NVIDIA GPU with CUDA, 10-50x faster than CPU  
- **Memory**: Models range from 500MB to 2GB each
- **First Request**: Slower due to model loading, subsequent requests are fast

## Model Management

Models are automatically downloaded from Hugging Face Hub and cached in `/root/.cache/huggingface`. To persist models across container restarts, mount this directory:

```bash
-v pytorch_tts_cache:/root/.cache/huggingface
```

## Troubleshooting

### Model Loading Issues
```bash
# Check model compatibility
curl http://localhost:8000/models

# View logs
docker logs pytorch-tts-server
```

### GPU Not Detected
```bash
# Verify GPU support
docker run --gpus all pytorch-tts-server python -c "import torch; print(torch.cuda.is_available())"
```

### Memory Issues
```bash
# Increase Docker memory limit or use smaller models
docker run -m 4g pytorch-tts-server
```

## Contributing

1. Fork the repository
2. Add support for new TTS models in `app.py`
3. Update `SUPPORTED_MODELS` configuration
4. Test with various text inputs
5. Submit pull request

## License

MIT License - see LICENSE file for details.
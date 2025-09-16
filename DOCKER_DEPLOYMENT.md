# Docker Deployment Guide for Bark TTS Integration

This guide covers the Docker configuration for the PyTorch TTS server with Bark model support in the Subway Surfers project.

## Architecture Overview

The system includes multiple TTS options:
- **PyTorch TTS Server**: Bark models from Suno AI (primary)
- **AllTalk TTS Server**: Coqui XTTS with voice cloning (alternative)

## Quick Start

### Development Environment (Mock TTS - 200MB RAM)
```bash
./deploy-tts.sh -e development
```

### Staging Environment (Small Models - 6GB RAM)
```bash
./deploy-tts.sh -e staging -b
```

### Production Environment (Full Models - 9GB+ RAM)
```bash
./deploy-tts.sh -e production -b
```

### Production with GPU Support
```bash
./deploy-tts.sh -e production -g -b
```

## Manual Deployment

### 1. Development with Mock Server
```bash
# Uses docker-compose.override.yml automatically
docker-compose -f docker-compose.local-stack.yml up -d
```

### 2. Production with Small Models
```bash
# Set environment variables for small models
export SUNO_USE_SMALL_MODELS=true
export SUNO_OFFLOAD_CPU=true

docker-compose -f docker-compose.local-stack.yml up -d pytorch-tts
```

### 3. Production with GPU
```bash
# Build GPU-optimized image
docker build -f pytorch-tts-server/Dockerfile.gpu -t pytorch-tts:gpu pytorch-tts-server/

# Run with GPU support
docker-compose -f docker-compose.production.yml up -d pytorch-tts-gpu
```

## Memory Requirements

| Configuration | Memory Usage | CPU Cores | GPU | Startup Time |
|--------------|--------------|-----------|-----|--------------|
| Mock Server | 200MB | 1 | No | 5s |
| Small Models | 3-6GB | 4 | No | 60s |
| Full Models (CPU) | 6-9GB | 8 | No | 120s |
| Full Models (GPU) | 8-12GB | 4 | Yes | 90s |

## Configuration Options

### Environment Variables

#### PyTorch TTS Server
- `SUNO_USE_SMALL_MODELS`: Use smaller Bark models (true/false)
- `SUNO_OFFLOAD_CPU`: Offload model to CPU (true/false)
- `PYTORCH_CUDA_ALLOC_CONF`: CUDA memory allocation config
- `TRANSFORMERS_CACHE`: Cache directory for models
- `PRELOAD_MODELS`: Comma-separated list of models to preload

#### Main Application
- `PYTORCH_TTS_ENDPOINT`: TTS server endpoint (default: http://pytorch-tts:8000)
- `PYTORCH_TTS_MODEL`: Model to use (default: suno/bark)

### Docker Compose Files

1. **docker-compose.local-stack.yml**: Main configuration with all services
2. **docker-compose.override.yml**: Development overrides (auto-applied)
3. **docker-compose.memory-optimized.yml**: Memory-constrained deployments
4. **docker-compose.production.yml**: Production with load balancing and monitoring

## Service Endpoints

| Service | Development | Production |
|---------|------------|------------|
| Main App | http://localhost:5001 | http://localhost:5001 |
| PyTorch TTS | http://localhost:8001 | http://localhost:8000 |
| AllTalk TTS | http://localhost:7851 | http://localhost:7851 |
| Whisper ASR | http://localhost:9000 | http://localhost:9000 |
| Grafana | - | http://localhost:3000 |
| Prometheus | - | http://localhost:9090 |

## Switching Between TTS Services

### Use PyTorch TTS with Bark (Default)
```yaml
environment:
  - PYTORCH_TTS_ENDPOINT=http://pytorch-tts:8000
  - PYTORCH_TTS_MODEL=suno/bark
```

### Use AllTalk TTS
```yaml
environment:
  - PYTORCH_TTS_ENDPOINT=http://alltalk-tts:7851
  - PYTORCH_TTS_MODEL=xtts
```

## Volume Mounts

### PyTorch TTS Volumes
- `pytorch_models`: Hugging Face model cache
- `pytorch_cache`: Transformers cache
- `./pytorch-tts-server/voices`: Custom voice samples
- `./temp`: Temporary audio files

### Persistent Data
All model data is persisted in Docker volumes to avoid re-downloading.

## Health Checks

Services include health checks with appropriate timeouts:
- Mock Server: 10s startup
- Small Models: 120s startup
- Full Models: 180s startup (GPU) / 300s (CPU)

## Monitoring

### Check Service Health
```bash
# All services
docker-compose ps

# Service logs
docker-compose logs -f pytorch-tts

# Health check
curl http://localhost:8001/health
```

### Resource Usage
```bash
# Container stats
docker stats

# Detailed metrics (production)
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

## Troubleshooting

### Out of Memory
1. Use small models: Set `SUNO_USE_SMALL_MODELS=true`
2. Enable CPU offloading: Set `SUNO_OFFLOAD_CPU=true`
3. Reduce batch size in application
4. Use mock server for development

### Slow Performance
1. Enable GPU support if available
2. Preload models on startup
3. Use Redis cache (uncomment in docker-compose)
4. Scale horizontally with multiple instances

### GPU Not Detected
1. Install NVIDIA Docker runtime
2. Check CUDA compatibility (requires CUDA 11.8+)
3. Verify with: `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi`

### Model Download Issues
1. Check internet connectivity
2. Verify Hugging Face access
3. Mount local model cache: `-v /path/to/models:/app/models`

## Clean Up

```bash
# Stop all services
docker-compose -f docker-compose.local-stack.yml down

# Remove volumes (caution: deletes downloaded models)
docker-compose -f docker-compose.local-stack.yml down -v

# Complete cleanup
./deploy-tts.sh -c -e development
```

## Advanced Configuration

### Custom Bark Voices
Place voice samples in `pytorch-tts-server/voices/` directory.

### Multi-GPU Setup
Edit `CUDA_VISIBLE_DEVICES` in docker-compose to assign specific GPUs.

### Load Balancing
Production configuration includes NGINX for load balancing between GPU and CPU instances.

### Scaling
```bash
# Scale PyTorch TTS instances
docker-compose -f docker-compose.production.yml up -d --scale pytorch-tts-cpu=3
```

## Security Considerations

1. All services run as non-root users
2. Minimal base images used
3. Health checks prevent unhealthy services
4. Network isolation between services
5. Resource limits prevent runaway consumption

## Performance Tips

1. **Development**: Use mock server for fastest iteration
2. **Testing**: Use small models with CPU offloading
3. **Production**: Use GPU with full models for best quality
4. **Caching**: Enable Redis for response caching
5. **Monitoring**: Use Grafana dashboards for performance tracking
# Bark TTS Deployment Guide
**Memory-Optimized Deployment for Subway Surfers Project**

Based on comprehensive memory analysis and optimization recommendations.

## Quick Start

### 1. Development Mode (Mock Server)
```bash
# Start mock TTS server with minimal memory footprint
docker-compose -f docker-compose.memory-optimized.yml up pytorch-tts-mock

# Test the deployment
curl http://localhost:8000/health
curl http://localhost:8000/voices
```

**Memory Usage**: ~512 MB total
**Best For**: Development, testing, CI/CD

### 2. Production Mode (Small Model)
```bash
# Start production-ready TTS with bark-small model
docker-compose -f docker-compose.memory-optimized.yml up pytorch-tts-small

# Test with actual synthesis
curl -X POST http://localhost:8001/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Welcome to Subway Surfers!", "voice": "narrator"}'
```

**Memory Usage**: ~6 GB total
**Best For**: Production, quality audio with reasonable resource usage

### 3. High-Quality Mode (GPU)
```bash
# Requires NVIDIA Docker runtime
docker-compose -f docker-compose.memory-optimized.yml up pytorch-tts-full-gpu

# Test high-quality synthesis
curl -X POST http://localhost:8002/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "This is the highest quality voice synthesis!", "voice": "announcer"}'
```

**Memory Usage**: ~12 GB system + 8 GB GPU
**Best For**: Maximum quality, fastest synthesis

## Memory Configuration Summary

| Deployment | System RAM | GPU Memory | Container Limit | Use Case |
|------------|------------|------------|-----------------|----------|
| Mock | 4 GB | - | 512 MB | Development |
| Small Model | 8 GB | 4 GB (optional) | 6 GB | Production |
| Full GPU | 16 GB | 8 GB | 12 GB | High Quality |
| Full CPU | 32 GB | - | 16 GB | CPU-only Production |

## Environment Variables

### Memory Optimization
```bash
# Use small models for memory efficiency
export SUNO_USE_SMALL_MODELS=True

# Enable CPU offloading for low-memory systems
export SUNO_OFFLOAD_CPU=True

# PyTorch memory allocation
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:2048

# Model caching
export TRANSFORMERS_CACHE=/app/cache
```

### Performance Tuning
```bash
# CPU threading (CPU-only deployments)
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8

# GPU visibility
export CUDA_VISIBLE_DEVICES=0

# Logging
export LOG_LEVEL=info
```

## Load Balancing Setup

### High Availability Configuration
```bash
# Start multiple TTS instances with load balancer
docker-compose -f docker-compose.memory-optimized.yml up \
  pytorch-tts-mock \
  pytorch-tts-small \
  nginx-lb

# Access through load balancer
curl http://localhost:8080/health
```

### Scaling Strategy
```bash
# Scale specific service
docker-compose -f docker-compose.memory-optimized.yml up --scale pytorch-tts-small=3

# Monitor with Prometheus
docker-compose -f docker-compose.memory-optimized.yml up prometheus
# Visit http://localhost:9090
```

## Health Checks and Monitoring

### Built-in Health Checks
```bash
# Basic health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "pytorch_loaded": true,
  "device": "cpu",
  "mock_mode": false
}
```

### Memory Monitoring
```bash
# Check container memory usage
docker stats

# Container-specific monitoring
docker exec pytorch-tts-small ps aux
docker exec pytorch-tts-small free -h
```

### Application Metrics
```bash
# Voice synthesis test
curl -X POST http://localhost:8000/test-voices

# Performance metrics
curl http://localhost:8000/voices | jq '.voices | length'
```

## Troubleshooting

### Common Memory Issues

**1. Out of Memory (OOM)**
```bash
# Check docker logs
docker logs pytorch-tts-small

# Increase memory limit
# Edit docker-compose.memory-optimized.yml:
#   limits:
#     memory: 8G  # Increase from 6G
```

**2. Slow Model Loading**
```bash
# Enable CPU offloading
docker exec pytorch-tts-small env | grep SUNO_OFFLOAD_CPU

# Check available disk space for caching
docker exec pytorch-tts-small df -h /app/cache
```

**3. GPU Memory Issues**
```bash
# Check GPU memory
nvidia-smi

# Clear GPU cache
docker exec pytorch-tts-full-gpu python -c "
import torch
torch.cuda.empty_cache()
print(f'GPU memory: {torch.cuda.memory_allocated()/1024/1024:.1f} MB')
"
```

### Performance Optimization

**1. Cold Start Optimization**
```bash
# Pre-warm models by making initial request
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "warmup", "voice": "narrator"}'
```

**2. Cache Optimization**
```bash
# Check cache usage
docker exec pytorch-tts-small du -sh /app/cache

# Clear cache if needed
docker exec pytorch-tts-small rm -rf /app/cache/*
```

**3. Connection Optimization**
```bash
# Use keep-alive connections
curl -H "Connection: keep-alive" http://localhost:8000/health

# Monitor connection pool
docker exec nginx-lb nginx -T | grep keepalive
```

## Production Checklist

### Before Deployment
- [ ] System meets minimum memory requirements
- [ ] GPU drivers installed (if using GPU mode)
- [ ] Docker and docker-compose installed
- [ ] NVIDIA Docker runtime configured (GPU mode)
- [ ] Storage space available for model caching
- [ ] Network ports available (8000, 8001, 8002, 8080)

### After Deployment
- [ ] Health checks passing
- [ ] Memory usage within limits
- [ ] Test synthesis working
- [ ] Load balancer routing correctly
- [ ] Monitoring dashboards accessible
- [ ] Backup strategy in place

### Monitoring Setup
- [ ] Prometheus metrics collection
- [ ] Memory usage alerts configured
- [ ] Error rate monitoring
- [ ] Performance dashboards created
- [ ] Log aggregation configured

## Integration with Subway Surfers

### Environment Variables for Main Application
```bash
# Point to load balancer for high availability
export PYTORCH_TTS_ENDPOINT=http://localhost:8080

# Or point to specific instance
export PYTORCH_TTS_ENDPOINT=http://localhost:8001

# Model selection
export PYTORCH_TTS_MODEL=suno/bark-small  # or suno/bark

# Voice selection
export DEFAULT_VOICE=narrator
```

### Example Integration Code
```python
import requests
import os

TTS_ENDPOINT = os.getenv('PYTORCH_TTS_ENDPOINT', 'http://localhost:8000')
TTS_MODEL = os.getenv('PYTORCH_TTS_MODEL', 'suno/bark-small')

def generate_narration(text, voice='narrator'):
    response = requests.post(
        f'{TTS_ENDPOINT}/synthesize',
        json={
            'text': text,
            'voice': voice,
            'model': TTS_MODEL
        },
        timeout=120
    )

    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            return data['audio_data']  # Base64 encoded audio

    raise Exception(f"TTS failed: {response.status_code}")
```

## Security Considerations

### Network Security
```bash
# Restrict access to internal network only
# Add to docker-compose.yml:
#   networks:
#     internal:
#       driver: bridge
#       internal: true
```

### Resource Limits
```bash
# Always set memory limits to prevent OOM
# Always set CPU limits to prevent resource exhaustion
# Use health checks to detect and restart failed containers
```

### Model Security
```bash
# Use specific model versions
export PYTORCH_TTS_MODEL=suno/bark-small:v1.0.0

# Verify model checksums
# Implement model validation
```

## Support and Maintenance

### Log Files
```bash
# Application logs
docker logs pytorch-tts-small --tail 100 -f

# NGINX logs
docker logs nginx-lb --tail 100 -f

# System logs
journalctl -u docker -f
```

### Backup and Recovery
```bash
# Backup model cache
docker run --rm -v pytorch_cache:/cache -v $(pwd):/backup \
  alpine tar czf /backup/model-cache.tar.gz -C /cache .

# Restore model cache
docker run --rm -v pytorch_cache:/cache -v $(pwd):/backup \
  alpine tar xzf /backup/model-cache.tar.gz -C /cache
```

### Updates and Maintenance
```bash
# Update containers
docker-compose -f docker-compose.memory-optimized.yml pull
docker-compose -f docker-compose.memory-optimized.yml up -d

# Clean up old images
docker image prune -f

# Clean up unused volumes
docker volume prune -f
```

For detailed memory analysis and optimization recommendations, see `MEMORY_ANALYSIS_REPORT.md`.
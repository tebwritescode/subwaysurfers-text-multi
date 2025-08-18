# 🎮 Complete Local Subway Surfers Stack

A fully self-hosted solution with Bark TTS voices and local Whisper ASR. No external dependencies or API keys required!

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Subway Surfers │───→│  PyTorch TTS     │    │  Whisper ASR    │
│  Web App :5000  │    │  (Bark) :8000    │    │  Server :9000   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                           🐳 Docker Network
```

## 🎯 Features

### 🎤 **Bark TTS Voices**
- **Narrator** - Perfect for storytelling
- **Announcer** - Professional presentation voice  
- **Excited** - Enthusiastic and energetic
- **Calm** - Peaceful and relaxed
- **Deep** - Authoritative bass voice
- **10 Speaker Variations** - Different personality voices

### 🎧 **Local Whisper ASR**
- Word-level timestamps for perfect caption sync
- Multiple model sizes (tiny to large-v3)
- GPU acceleration support
- No internet required after setup

### 🚀 **Performance**
- **CPU Support** - Runs on any modern CPU
- **GPU Acceleration** - 10-50x faster with NVIDIA GPU
- **Smart Caching** - Models cached between runs
- **Memory Optimization** - Automatic CPU offloading for low VRAM

## 🚀 Quick Start

### 1. **Prerequisites**
```bash
# Required
docker-compose >= 1.29.0
Docker Desktop (with 8GB+ RAM allocated)

# Optional for GPU acceleration
nvidia-docker2 
NVIDIA GPU with 4GB+ VRAM
```

### 2. **Launch the Stack**
```bash
# Clone repository
git clone <repo-url>
cd subwaysurfers-text-multi

# Start all services
docker-compose -f docker-compose.local-stack.yml up -d

# View logs
docker-compose -f docker-compose.local-stack.yml logs -f
```

### 3. **Test Bark Voices**
```bash
# Wait for services to start (2-3 minutes)
docker-compose -f docker-compose.local-stack.yml ps

# Test voice generation
python test-bark-voices.py

# Listen to generated samples in ./voice_samples/
```

### 4. **Access Services**
- **Subway Surfers App**: http://localhost:5001
- **PyTorch TTS API**: http://localhost:8000/docs  
- **Whisper ASR API**: http://localhost:9000/docs

## 🔧 Configuration Options

### **CPU-Only Setup** (Default)
```yaml
# docker-compose.local-stack.yml
environment:
  - SUNO_OFFLOAD_CPU=true      # Enable CPU offloading
  - SUNO_USE_SMALL_MODELS=true # Use smaller Bark model
```

### **GPU Acceleration** 
```yaml
# Uncomment in docker-compose.local-stack.yml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### **Memory Optimization**
| Setting | VRAM | Speed | Quality |
|---------|------|--------|---------|
| `SUNO_USE_SMALL_MODELS=true` | 2GB | Fast | Good |
| `SUNO_USE_SMALL_MODELS=false` | 6GB+ | Slower | Best |
| `SUNO_OFFLOAD_CPU=true` | Any | Slower | Same |

## 🎯 Usage Examples

### **API Testing**
```bash
# Test PyTorch TTS health
curl http://localhost:8000/health

# Get available voices
curl http://localhost:8000/voices

# Generate speech
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to Subway Surfers!",
    "voice": "announcer", 
    "model": "suno/bark"
  }'

# Test Whisper ASR
curl -X POST http://localhost:9000/transcribe \
  -F "audio_file=@sample.wav" \
  -F "model=base" \
  -F "word_timestamps=true"
```

### **Web Interface Usage**
1. Open http://localhost:5000
2. Paste article URL or text
3. Select voice: `narrator`, `announcer`, `excited`, `calm`, or `deep`
4. Click "Generate Video"
5. Watch real-time progress
6. Download your Subway Surfers video!

## 📊 Performance Expectations

### **First Run (Model Download)**
- Bark Model: ~1.5GB download, 5-10 minutes
- Whisper Base: ~150MB download, 1-2 minutes  
- Subsequent runs: Instant startup from cache

### **Generation Times**
| Hardware | Bark TTS (30s audio) | Whisper ASR (30s audio) |
|----------|---------------------|-------------------------|
| CPU Only | 60-120 seconds | 10-30 seconds |
| RTX 3060 | 10-20 seconds | 2-5 seconds |
| RTX 4090 | 5-10 seconds | 1-2 seconds |

### **Resource Usage**
| Component | CPU | RAM | VRAM | Disk |
|-----------|-----|-----|------|------|
| Subway App | Low | 1GB | - | 2GB |
| PyTorch TTS | High | 4GB | 6GB | 5GB |
| Whisper ASR | Medium | 2GB | 2GB | 1GB |

## 🛠️ Troubleshooting

### **Common Issues**

**🔴 "CUDA out of memory"**
```bash
# Enable CPU offloading
export SUNO_OFFLOAD_CPU=true
export SUNO_USE_SMALL_MODELS=true
```

**🔴 "Model download timeout"**
```bash
# Increase Docker timeout
export COMPOSE_HTTP_TIMEOUT=300
export DOCKER_CLIENT_TIMEOUT=300
```

**🔴 "PyTorch TTS not responding"** 
```bash
# Check model loading progress
docker-compose -f docker-compose.local-stack.yml logs pytorch-tts
```

**🔴 "Port already in use"**
```bash
# Change ports in docker-compose.local-stack.yml
ports:
  - "5001:5000"  # Subway Surfers → localhost:5001
  - "8001:8000"  # PyTorch TTS → localhost:8001  
  - "9001:9000"  # Whisper ASR → localhost:9001
```

### **Performance Tuning**

**For Low-End Hardware:**
```bash
# Use CPU-optimized settings
environment:
  - SUNO_USE_SMALL_MODELS=true
  - SUNO_OFFLOAD_CPU=true
  - PRELOAD_MODEL=tiny        # Whisper tiny model
```

**For High-End Hardware:**
```bash
# Use quality-optimized settings  
environment:
  - SUNO_USE_SMALL_MODELS=false
  - SUNO_OFFLOAD_CPU=false
  - PRELOAD_MODEL=large-v3    # Best Whisper model
```

## 📁 File Structure

```
subwaysurfers-text-multi/
├── docker-compose.local-stack.yml    # Complete stack
├── test-bark-voices.py              # Voice testing script
├── LOCAL-STACK.md                   # This documentation
├── 
├── pytorch-tts-server/              # Bark TTS service
│   ├── Dockerfile
│   ├── app.py                       # FastAPI server
│   ├── requirements.txt
│   └── start.sh
├── 
├── whisper-asr-server/              # Whisper ASR service  
│   ├── Dockerfile
│   ├── app.py                       # FastAPI server
│   ├── requirements.txt
│   └── start.sh
├── 
├── voice_samples/                   # Generated test samples
├── static/                          # Background videos
├── final_videos/                    # Generated videos
└── models/                          # Cached AI models
```

## 🎥 Voice Samples

After running the test script, you'll have sample audio files:

```bash
voice_samples/
├── narrator_sample.wav       # Story narration
├── announcer_sample.wav      # Professional presentation
├── excited_sample.wav        # Enthusiastic energy
├── calm_sample.wav          # Peaceful relaxation  
├── deep_sample.wav          # Authoritative bass
├── batch_narrator_test.wav   # Batch test samples
├── batch_announcer_test.wav
├── batch_excited_test.wav
├── batch_calm_test.wav
└── batch_deep_test.wav
```

## 🚀 Production Deployment

### **Docker Swarm**
```bash
# Deploy to swarm
docker stack deploy -c docker-compose.local-stack.yml subway-stack
```

### **Kubernetes**
```bash
# Convert to k8s manifests
kompose convert -f docker-compose.local-stack.yml
kubectl apply -f .
```

### **Cloud Deployment**
- **AWS ECS** - Use GPU-enabled container instances
- **Google Cloud Run** - CPU-only deployment
- **Azure Container Instances** - With GPU support

## 🎮 Ready to Create Videos!

Your complete local Subway Surfers stack is now running with:

✅ **High-quality Bark voices** - No more robotic TTS  
✅ **Accurate Whisper captions** - Perfect timing sync  
✅ **Complete privacy** - Everything runs locally  
✅ **No API costs** - Use unlimited generations  
✅ **GPU acceleration** - Fast video creation  

**Start creating engaging Subway Surfers videos with premium voices!** 🎬
# 🎮 Subway Surfers Text-to-Video Generator

> A comprehensive Flask web application that automatically generates engaging Subway Surfers-style videos with text-to-speech narration and synchronized captions from articles or text input.

![Version](https://img.shields.io/badge/Version-1.1.22-blue)
![Python](https://img.shields.io/badge/Python-3.12-green)
![Flask](https://img.shields.io/badge/Flask-3.0.3-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ⚡ Overview

Transform articles and text into captivating TikTok-style videos with Subway Surfers gameplay backgrounds. This application helps users absorb information more effectively by creating engaging video content that captures and maintains attention.

---

## Screenshots

<details>
  <summary><i>Click to show screenshots</i></summary>

![Generate](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_5.17.25_PM.png)
![Link](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.14.47_PM.png)
![Progress Bar](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.11.06_PM.png)
![View Current 1](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.12.03_PM.png)
![View Current 2](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_5.17.41_PM.png)
![Browse](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.29.02_PM.png)

</details>

## 🆕 What's New in v1.1.22

### 🎯 Latest Release - Production Ready
- **✅ Bark TTS Integration**: High-quality neural TTS with natural voice synthesis
- **✅ WhisperASR Integration**: Perfect caption timing synchronization
- **✅ Multi-section Processing**: Handles long texts without truncation
- **✅ Configurable Caption Timing**: Adjustable caption offset for perfect sync
- **✅ Docker Optimized**: Streamlined build with proper dependency management
- **✅ Clean Codebase**: Removed test outputs and temporary files

### 🚀 Previous Features (v1.1.x)
- **✅ Real-time Progress Tracking**: Live updates during video generation
- **✅ Multiple Voice Options**: Support for various TikTok voices
- **✅ Browse Generated Videos**: View and manage previously created content
- **✅ Error Recovery**: Resilient handling of TTS and video processing failures

*For complete version history, see [version.py](version.py)*

## ✨ Features

### 🎬 **Video Generation**
- Automatic text extraction from URLs or direct input
- Multiple TikTok voice options for narration
- Synchronized captions with adjustable timing
- Background gameplay from multiple games (Subway Surfers, Minecraft, etc.)
- Real-time progress tracking during generation

### 🎙️ **Text-to-Speech**
- High-quality TikTok voices
- Bark TTS neural synthesis with realistic intonation
- Multiple voice presets and languages support
- Adjustable speech speed
- Support for long texts with automatic sectioning
- Clean text preprocessing for better pronunciation

### 📱 **User Interface**
- Clean, modern web interface
- Mobile-responsive design
- Real-time generation progress with visual indicators
- Video browsing and management
- Flash message notifications

### 🔧 **Technical Features**
- WhisperASR integration for accurate speech timing
- Bark TTS with PyTorch backend support
- Docker containerization for easy deployment
- Configurable caption timing offset
- Robust error handling and recovery
- Support for custom video sources
- Automatic fallback between TTS providers

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ and pip
- FFmpeg installed on your system
- OR Docker and Docker Compose

### Installation Options

#### **Option 1: Docker** (Recommended)

```bash
# Pull and run the latest version
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Or use Docker Compose
docker-compose up -d
```

#### **Option 2: Local Development**

```bash
# Clone the repository
git clone https://github.com/tebwritescode/subwaysurfers-text-multi.git
cd subwaysurfers-text-multi

# Set up Python environment
python3.12 -m venv .venv
source ./.venv/bin/activate

# Install dependencies
pip install -r requirements-pip.txt

# Download required models
# 1. Download Vosk English Model from:
#    https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip
#    Extract to ./static/vosk-model-en-us-0.22/

# 2. Add background videos to ./static/
#    Download sample: https://drive.google.com/file/d/1ZyFZKIB1HiZM_XDQPRRiiAIvU4sgl10k/view

# Start the application
python app.py
# Or with Flask
flask run
```

Access the application at `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `5000` | Web server port |
| `WHISPER_ASR_URL` | `http://localhost:9000` | WhisperASR service URL |
| `CAPTION_TIMING_OFFSET` | `0.25` | Caption display offset in seconds |
| `SOURCE_VIDEO_DIR` | `./static` | Directory containing background videos |
| `MODEL_PATH` | `./static/vosk-model-en-us-0.22` | Path to Vosk speech model |
| `DOCKER_ENV` | `false` | Set to `true` when running in Docker |
| `USE_COQUI_TTS` | `false` | Set to `true` to use Coqui TTS instead of TikTok TTS |
| `COQUI_TTS_ENDPOINT` | `http://localhost:5000` | Coqui TTS server endpoint URL |
| `SPEAKER_WAV_PATH` | | Path to speaker reference audio for voice cloning |
| `PYTORCH_TTS_ENDPOINT` | | PyTorch TTS server endpoint for Bark support |
| `PYTORCH_TTS_MODEL` | `bark` | TTS model to use (bark for Bark TTS) |
| `BARK_VOICE_PRESET` | `v2/en_speaker_1` | Bark voice preset selection |
| `BARK_USE_SMALL` | `false` | Use small Bark model to reduce memory |
| `BARK_CPU_OFFLOAD` | `true` | Offload model to CPU to save GPU memory |
| `BARK_MOCK_MODE` | `false` | Use mock Bark for testing (200MB memory) |

### Docker Deployment

```bash
# Using TikTok TTS (default - no external server needed)
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e CAPTION_TIMING_OFFSET=-0.1 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Using external PyTorch TTS server with custom voices
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e PYTORCH_TTS_ENDPOINT=http://your-pytorch-tts:8000 \
  -e PYTORCH_TTS_MODEL=drewThomasson/Morgan_freeman_xtts_model \
  -e SPEAKER_EMBEDDING_PATH=/app/embeddings/morgan_freeman.bin \
  -v /path/to/videos:/app/static \
  -v /path/to/embeddings:/app/embeddings \
  tebwritescode/subwaysurfers-text20:latest

# Using Bark TTS with PyTorch server (high quality neural TTS)
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e PYTORCH_TTS_ENDPOINT=http://your-pytorch-tts:8000 \
  -e PYTORCH_TTS_MODEL=bark \
  -e BARK_VOICE_PRESET=v2/en_speaker_6 \
  -e BARK_USE_SMALL=false \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Using Docker Compose
docker-compose up -d
```

**Docker Hub**: https://hub.docker.com/r/tebwritescode/subwaysurfers-text20

## 🎙️ Bark TTS Integration

### Overview

Bark is a state-of-the-art neural text-to-speech model that generates highly realistic and expressive speech. Unlike traditional TTS systems, Bark can:

- Generate natural-sounding speech with realistic intonation and emotion
- Support multiple languages and accents
- Produce non-speech sounds like laughter, sighs, and music
- Maintain consistent voice characteristics across long texts
- Handle complex punctuation and formatting naturally

### Setup Instructions

#### 1. **PyTorch TTS Server Setup**

Bark requires a PyTorch TTS server to handle the neural model processing:

```bash
# Start the PyTorch TTS server with Bark support
docker run -d --name pytorch-tts \
  --gpus all \
  -p 8000:8000 \
  -e MODEL=bark \
  -e USE_GPU=true \
  pytorch-tts-server:latest

# For CPU-only deployment (slower but uses less memory)
docker run -d --name pytorch-tts \
  -p 8000:8000 \
  -e MODEL=bark \
  -e USE_GPU=false \
  -e CPU_THREADS=4 \
  pytorch-tts-server:latest
```

#### 2. **Configure Subway Surfers App**

```bash
# Set environment variables to use Bark
export PYTORCH_TTS_ENDPOINT=http://localhost:8000
export PYTORCH_TTS_MODEL=bark
export BARK_VOICE_PRESET=v2/en_speaker_1
```

### Available Voice Presets

Bark includes numerous high-quality voice presets:

**English Voices:**
- `v2/en_speaker_0` - Male, neutral American accent
- `v2/en_speaker_1` - Female, neutral American accent
- `v2/en_speaker_2` - Male, deep voice
- `v2/en_speaker_3` - Female, expressive voice
- `v2/en_speaker_4` - Male, British accent
- `v2/en_speaker_5` - Female, soft voice
- `v2/en_speaker_6` - Male, announcer style
- `v2/en_speaker_7` - Female, younger voice
- `v2/en_speaker_8` - Male, older voice
- `v2/en_speaker_9` - Female, professional voice

**Multilingual Support:**
- German: `v2/de_speaker_0` to `v2/de_speaker_9`
- Spanish: `v2/es_speaker_0` to `v2/es_speaker_9`
- French: `v2/fr_speaker_0` to `v2/fr_speaker_9`
- Hindi: `v2/hi_speaker_0` to `v2/hi_speaker_9`
- Italian: `v2/it_speaker_0` to `v2/it_speaker_9`
- Japanese: `v2/ja_speaker_0` to `v2/ja_speaker_9`
- Korean: `v2/ko_speaker_0` to `v2/ko_speaker_9`
- Polish: `v2/pl_speaker_0` to `v2/pl_speaker_9`
- Portuguese: `v2/pt_speaker_0` to `v2/pt_speaker_9`
- Russian: `v2/ru_speaker_0` to `v2/ru_speaker_9`
- Turkish: `v2/tr_speaker_0` to `v2/tr_speaker_9`
- Chinese: `v2/zh_speaker_0` to `v2/zh_speaker_9`

### Memory Requirements

Bark models have different memory footprints:

| Configuration | GPU Memory | System RAM | Quality | Speed |
|--------------|------------|------------|---------|--------|
| **Full Model (GPU)** | 6-9 GB | 4 GB | Highest | Fast |
| **Full Model (CPU)** | - | 8-12 GB | Highest | Slow |
| **Small Model** | 2-3 GB | 2 GB | Good | Medium |
| **Mock Mode** | - | 200 MB | Test only | Instant |

**Memory Optimization Tips:**
- Use `BARK_USE_SMALL=true` for systems with limited memory
- Enable `BARK_CPU_OFFLOAD=true` to reduce GPU memory usage
- Use `BARK_MOCK_MODE=true` for development and testing
- Consider batch processing for long texts to manage memory

### Configuration Options

```bash
# Full configuration example
docker run -p 5000:5000 \
  -e PYTORCH_TTS_ENDPOINT=http://pytorch-tts:8000 \
  -e PYTORCH_TTS_MODEL=bark \
  -e BARK_VOICE_PRESET=v2/en_speaker_1 \
  -e BARK_USE_SMALL=false \
  -e BARK_CPU_OFFLOAD=true \
  -e BARK_MOCK_MODE=false \
  -e WHISPER_ASR_URL=http://whisper:9000 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

### Advanced Features

**Custom Voice Fine-tuning:**
```python
# Example configuration for custom voice characteristics
{
  "text_temp": 0.7,      # Text generation temperature (0.5-1.0)
  "waveform_temp": 0.7,  # Audio generation temperature (0.5-1.0)
  "min_eos_p": 0.05,     # Minimum end-of-speech probability
  "max_gen_duration": 30 # Maximum generation duration in seconds
}
```

**Progress Indicators:**
Bark TTS integration includes real-time progress indicators:
- Text preprocessing progress
- Model loading status
- Audio generation progress
- Post-processing status

## 📖 Usage Guide

### **Generating Videos**
1. Navigate to the home page
2. Enter text directly or provide a URL
3. Select a voice from the dropdown (Jessie, Brian, Stitch, Echo, etc.)
4. Choose speech speed (optional)
5. Click "Generate" and watch real-time progress
6. Download or view the generated video

<<<<<<< Updated upstream

### **Background Videos**
The application randomly selects from:
- Subway Surfers gameplay
- Minecraft parkour
- Pokemon gameplay
- Factorio automation
- StarCraft matches
- Satisfying slice videos

## 🏗️ Architecture

```
subwaysurfers-text-multi/
├── 📄 app.py                # Flask application and routes
├── 📄 sub.py                # Core video generation logic
├── 📄 tiktokvoice.py        # TikTok TTS integration
├── 📄 whisper_timestamper.py # WhisperASR timing sync
├── 📄 videomaker.py         # Video composition and captioning
├── 📄 cleantext.py          # Text preprocessing utilities
├── 📄 version.py            # Version tracking and history
├── 📄 requirements-pip.txt   # Python dependencies
├── 📄 requirements-docker.txt # Docker-specific dependencies
├── 📄 Dockerfile            # Container configuration
├── 📄 docker-compose.yml    # Docker composition
├── 📁 templates/            # HTML templates
│   ├── index.html          # Main generation interface
│   ├── videos.html         # Video browser
│   ├── progress.html       # Progress tracking
│   └── output.html         # Video display page
├── 📁 static/              # Static assets
│   ├── styles.css          # Application styles
│   ├── *.mp4               # Background videos
│   └── vosk-model-en-us-0.22/ # Speech recognition model
└── 📁 final_videos/        # Generated video storage
```

### Tech Stack
- **Backend**: Python 3.12 + Flask
- **TTS**: TikTok Voice API + Bark Neural TTS + PyTorch Server
- **Speech Recognition**: Vosk + WhisperASR
- **Video Processing**: MoviePy + FFmpeg + OpenCV
- **Frontend**: HTML + CSS + JavaScript
- **Containerization**: Docker + Docker Compose

## 🔐 Security

- Input validation for all user submissions
- URL validation to prevent malicious inputs
- Secure file handling with sanitized filenames
- Process isolation in Docker containers
- No user authentication required (public tool)

## 🛠️ Development

### Running Tests
```bash
# Run with test data
python app.py --test

# Clean generated videos
./clean.sh

# Process multiple texts
./concat.sh
```

### Building Docker Image
```bash
# Build multi-arch image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t tebwritescode/subwaysurfers-text20:latest \
  -t tebwritescode/subwaysurfers-text20:v1.1.22 \
  --push .
```

## 🐛 Known Issues

- Large videos may take several minutes to generate
- Some special characters in text may cause TTS issues
- Browser may timeout on very long texts (use smaller sections)
- WhisperASR server required for optimal caption timing
- Bark TTS requires significant memory (6-9GB for full model)

## 📊 Performance

- Average generation time: 2-5 minutes per minute of video
- Supports texts up to 10,000 words
- Optimized for videos under 10 minutes
- Multi-section processing for long texts
- Bark TTS: 10-30 seconds per sentence (depending on hardware)

## 🔧 Troubleshooting Bark TTS

### Common Issues and Solutions

**1. Out of Memory Errors**
```bash
# Solution 1: Use the small model
export BARK_USE_SMALL=true

# Solution 2: Enable CPU offloading
export BARK_CPU_OFFLOAD=true

# Solution 3: Use mock mode for testing
export BARK_MOCK_MODE=true
```

**2. Slow Generation Speed**
- Ensure GPU is properly configured with CUDA support
- Use batch processing for long texts
- Consider using the small model for faster generation
- Reduce `max_gen_duration` parameter

**3. Connection Refused to PyTorch Server**
```bash
# Check if the server is running
docker ps | grep pytorch-tts

# Check server logs
docker logs pytorch-tts

# Verify network connectivity
curl http://localhost:8000/health
```

**4. Voice Preset Not Found**
- Verify the preset name format (e.g., `v2/en_speaker_1`)
- Check available presets in server documentation
- Fall back to default preset: `v2/en_speaker_0`

**5. Audio Quality Issues**
- Adjust temperature parameters (text_temp, waveform_temp)
- Try different voice presets for better match
- Ensure input text is properly formatted and cleaned
- Check for special characters or unsupported symbols

### Fallback Behavior

The application includes automatic fallback mechanisms:

1. **Primary**: Bark TTS (if PyTorch server available)
2. **Secondary**: Coqui TTS (if configured)
3. **Tertiary**: TikTok TTS API (default fallback)
4. **Emergency**: Pre-generated placeholder audio

Configure fallback priority:
```bash
export TTS_FALLBACK_CHAIN="bark,coqui,tiktok"
export TTS_FALLBACK_TIMEOUT=30  # seconds before fallback
```

### Memory Optimization Tips

**For Limited Memory Systems:**
```bash
# Minimal memory configuration
docker run -p 5000:5000 \
  -e PYTORCH_TTS_ENDPOINT=http://pytorch-tts:8000 \
  -e BARK_USE_SMALL=true \
  -e BARK_CPU_OFFLOAD=true \
  -e MAX_TEXT_LENGTH=500 \
  --memory="4g" \
  --memory-swap="8g" \
  tebwritescode/subwaysurfers-text20:latest
```

**GPU Memory Management:**
```python
# Set GPU memory growth
export TF_FORCE_GPU_ALLOW_GROWTH=true
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

## 🚀 Roadmap

- [x] Bark TTS integration with neural voice synthesis
- [ ] Offload transcoding to separate container for scalability
- [ ] Source video selection dropdown in UI
- [ ] Upload custom background videos via web interface
- [ ] Additional TTS voice providers (ElevenLabs, Azure)
- [ ] Real-time preview during generation
- [ ] Batch processing for multiple articles
- [ ] Custom Bark voice training support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Test thoroughly with various text inputs
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- TikTok for voice synthesis technology
- Vosk for offline speech recognition
- WhisperASR for accurate timing synchronization
- The open source community for various dependencies

---

**Created by**: [tebbydog0605](https://github.com/tebbydog0605)  
**Docker Hub**: [tebwritescode](https://hub.docker.com/u/tebwritescode)  
**Website**: [teb.codes](https://teb.codes)

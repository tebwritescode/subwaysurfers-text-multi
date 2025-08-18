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
- Docker containerization for easy deployment
- Configurable caption timing offset
- Robust error handling and recovery
- Support for custom video sources

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

# Using a specific video file

# Using Docker Compose
docker-compose up -d
```

**Docker Hub**: https://hub.docker.com/r/tebwritescode/subwaysurfers-text20

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
- **TTS**: TikTok Voice API integration
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

## 📊 Performance

- Average generation time: 2-5 minutes per minute of video
- Supports texts up to 10,000 words
- Optimized for videos under 10 minutes
- Multi-section processing for long texts

## 🚀 Roadmap

- [ ] Offload transcoding to separate container for scalability
- [ ] Source video selection dropdown in UI
- [ ] Upload custom background videos via web interface
- [ ] Additional TTS voice providers
- [ ] Real-time preview during generation
- [ ] Batch processing for multiple articles

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

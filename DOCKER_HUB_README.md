# Subway Surfers Text-to-Video Generator

Transform articles and text into engaging TikTok-style videos with synchronized captions and Subway Surfers gameplay background.

## Features

- 🎬 **Automated Video Generation**: Convert text/URLs into vertical videos
- 🗣️ **TikTok TTS**: Multiple voices and accents (free, no API key required)
- 📝 **Precise Caption Timing**: WhisperASR integration for word-level synchronization
- 🎮 **Subway Surfers Background**: Engaging gameplay footage
- 📊 **Queue System**: Background processing with retry mechanism
- 📈 **Real-time Progress**: Server-Sent Events for live updates
- 🐳 **Docker Ready**: Multi-architecture support (AMD64/ARM64)

## Quick Start

### Using Docker (Recommended)

```bash
# Basic usage with directory of videos
docker run -p 5000:5000 \
  -v /path/to/your/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

### With WhisperASR Server (Better Caption Timing)

```bash
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e CAPTION_TIMING_OFFSET=-0.1 \
  -v /path/to/your/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Flask server port |
| `WHISPER_ASR_URL` | http://whisper-asr:9000 | WhisperASR server endpoint (optional) |
| `CAPTION_TIMING_OFFSET` | 0.25 | Caption display offset in seconds (recommend -0.1) |
| `SOURCE_VIDEO_DIR` | /app/static | Directory containing background videos |
| `MODEL_PATH` | /app/static/vosk-model-en-us-0.22 | Vosk speech model path |

## Volume Mounts

- `/app/static` - Mount your background videos here (>50MB MP4 files)
- `/app/final_videos` - Generated videos output directory

## Supported Platforms

- ✅ Linux AMD64 (x86_64)
- ✅ Linux ARM64 (Apple Silicon, Raspberry Pi 4/5)
- ✅ macOS (via Docker Desktop)
- ✅ Windows (via Docker Desktop)

## System Requirements

**Minimum:**
- 2GB RAM
- 2 CPU cores
- 5GB disk space

**Recommended:**
- 4GB RAM
- 4 CPU cores
- 10GB disk space
- WhisperASR server for better caption timing (additional 2-4GB RAM)

## Usage

1. **Start the container** using one of the commands above
2. **Access the web interface** at `http://localhost:5000`
3. **Paste article URL or text** into the input field
4. **Click Submit** and wait for processing
5. **Watch your video** directly in the browser or download it

## TTS Voices

The application uses TikTok TTS with multiple voice options:

### Character Voices
- Stitch (Disney)
- C3PO (Star Wars)
- Ghostface (Scream)
- Chewbacca

### Regional Accents
- US English (multiple)
- UK English (multiple)
- Australian English

### Special Voices
- Narrator
- Rocket
- And many more!

## Caption Timing

Two timing methods with automatic fallback:

1. **WhisperASR** (Recommended): Word-level timing from speech recognition
   - Requires external WhisperASR server
   - Extremely accurate synchronization
   - Set `WHISPER_ASR_URL` environment variable

2. **Simple Timing** (Fallback): Even word distribution
   - Used when Whisper unavailable
   - Minimum 0.2s per word
   - Still produces good results

## Multi-Section Processing

Long texts are automatically split into sections:
- Each section processed independently
- Seamless concatenation with FFmpeg
- Avoids timeout issues
- Perfect for long articles

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs <container-id>

# Verify port not in use
lsof -i :5000  # macOS/Linux
```

### No videos generating
- Ensure background videos exist in mounted directory (>50MB MP4 files)
- Check container logs for errors
- Verify you have enough disk space

### Caption timing off
- Try `CAPTION_TIMING_OFFSET=-0.1` or `-0.2`
- Use WhisperASR server for better timing
- Check logs for timing fallback warnings

## Docker Hub Tags

- `latest` - Stable release (v1.1.22)
- `v1.1.22` - Current stable version
- `v1.1.21` - Previous release
- `v1.1.20` - Older release

## Source Code

GitHub: [tebwritescode/subwaysurfers-text-multi](https://github.com/tebwritescode/subwaysurfers-text-multi)

## License

MIT License - See repository for details

## Version

Current stable version: **v1.1.22**

### What's in v1.1.22?
- ✅ Cleaned and sanitized codebase
- ✅ TikTok TTS with multiple voices
- ✅ WhisperASR integration for caption timing
- ✅ Queue-based processing system
- ✅ Configurable caption timing offset
- ✅ Multi-architecture Docker builds
- ✅ Environment variable configuration

### Roadmap
- ElevenLabs TTS integration (premium voices)
- ONNX voice support (local high-quality TTS)
- Source video selection UI
- Web upload for custom videos

---

**Note**: For experimental features like Bark TTS and ElevenLabs, see the `beta-v1.1.23` branch on GitHub.

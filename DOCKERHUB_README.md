# Subway Surfers Text-to-Video Generator

Transform article links into engaging Subway Surfers-style videos with text-to-speech narration and synchronized captions.

## Quick Start

```bash
# Using TikTok TTS (default)
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e CAPTION_TIMING_OFFSET=-0.1 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Using Coqui TTS with custom voices
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e USE_COQUI_TTS=true \
  -e COQUI_TTS_ENDPOINT=http://your-coqui-server:5000 \
  -e SPEAKER_WAV_PATH=/app/voices/morgan_freeman.wav \
  -v /path/to/videos:/app/static \
  -v /path/to/voice-samples:/app/voices \
  tebwritescode/subwaysurfers-text20:latest

# Using a specific video file
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e SOURCE_VIDEO_DIR=/app/static/surf.mp4 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_ASR_URL` | `http://host.docker.internal:9000` | URL of the WhisperASR server for speech-to-text caption timing synchronization |
| `PORT` | `5000` | Port number for the Flask web server |
| `CAPTION_TIMING_OFFSET` | `0.0` | Timing offset in seconds for caption display (negative values show captions earlier) |
| `MODEL_PATH` | `static/vosk-model-en-us-0.22` | Path to the Vosk speech recognition model |
| `SOURCE_VIDEO_DIR` | `static` | Path to a video file or directory. If a file, uses that specific video. If a directory, randomly selects from available videos |
| `FLASK_APP` | `app.py` | Flask application entry point |
| `DOCKER_ENV` | `true` | Indicates the application is running in a Docker container |
| `USE_COQUI_TTS` | `false` | Set to `true` to use Coqui TTS instead of TikTok TTS |
| `COQUI_TTS_ENDPOINT` | `http://localhost:5000` | Coqui TTS server endpoint URL |
| `SPEAKER_WAV_PATH` | | Path to speaker reference audio for voice cloning |

## Volume Mounts

Mount your video files to `/app/static` to make them available to the application:
```bash
-v /path/to/your/videos:/app/static
```

## Prerequisites

1. **WhisperASR Server**: Required for caption timing synchronization
2. **Background Videos**: Mount `.mp4` files to `/app/static`
3. **Vosk Model**: Included in the image

## Supported Architectures

- `linux/amd64`
- `linux/arm64`

## Usage

1. Access the web interface at `http://localhost:5000`
2. Paste an article URL or text
3. Select voice and speed options
4. Click Submit to generate video
5. Download the generated video with synchronized captions

## Source Code

https://github.com/tebwritescode/subwaysurfers-text-multi
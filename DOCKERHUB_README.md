# Subway Surfers Text-to-Video Generator

Turn articles or text into Subway Surfers-style vertical videos with text-to-speech
narration and word-by-word burned-in captions. Choose your TTS backend per video:
**TikTok** (free), **ElevenLabs** (API key), or a **Remote** TTS server.

## Quick Start

```bash
# Default: free TikTok voices. Mount a folder of .mp4 gameplay clips.
docker run -p 5000:5000 \
  -v /path/to/gameplay:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# ElevenLabs backend
docker run -p 5000:5000 \
  -e TTS_BACKEND=elevenlabs -e ELEVENLABS_API_KEY=sk_... \
  -v /path/to/gameplay:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Remote TTS backend (your own generator container)
docker run -p 5000:5000 \
  -e TTS_BACKEND=remote -e REMOTE_TTS_URL=http://my-tts-server:8080 \
  -v /path/to/gameplay:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

The backend and voice can also be chosen in the web UI per video.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TTS_BACKEND` | `tiktok` | Default backend: `tiktok`, `elevenlabs`, or `remote` |
| `ELEVENLABS_API_KEY` | – | API key for the ElevenLabs backend |
| `REMOTE_TTS_URL` | – | Remote TTS server (`POST {text, voice}` → audio bytes) |
| `REMOTE_TTS_VOICES_URL` | `${REMOTE_TTS_URL}/voices` | Remote backend voice list endpoint |
| `WHISPER_ASR_URL` | – | Optional whisper-asr-webservice for accurate caption timing |
| `CAPTION_TIMING_OFFSET` | `0.0` | Show captions earlier (seconds) |
| `CAPTION_FONT` | `DejaVu Sans` | Caption font (bundled in the image) |
| `SOURCE_VIDEO_DIR` | `static` | A `.mp4` file or a directory of clips (random pick) |
| `PORT` | `5000` | Web server port |

## Volume Mounts

Mount your gameplay clips to `/app/static` (a random `.mp4` is chosen per video):
```bash
-v /path/to/your/gameplay:/app/static
```
Optionally persist generated videos with `-v /path/to/out:/app/final_videos`.

## Supported Architectures

- `linux/amd64`
- `linux/arm64`

## Usage

1. Open `http://localhost:5000`
2. Paste an article URL or text
3. Pick a TTS backend + voice and a speed
4. Submit and watch real-time progress; view/download/manage videos under **Browse**

## Source Code

https://github.com/tebwritescode/subwaysurfers-text-multi

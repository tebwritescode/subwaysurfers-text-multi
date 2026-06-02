# 🎮 Subway Surfers Text-to-Video Generator

> A Flask web app that turns articles or text into engaging Subway Surfers-style
> vertical videos with text-to-speech narration and synchronized word-by-word
> captions — with **pluggable TTS backends** you can pick per video.

![Version](https://img.shields.io/badge/Version-1.3.0-blue)
![Python](https://img.shields.io/badge/Python-3.13-green)
![Flask](https://img.shields.io/badge/Flask-3.0.3-blue)
![Docker](https://img.shields.io/badge/Docker-multi--arch-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ⚡ Overview

Transform articles and text into captivating TikTok-style videos with gameplay
backgrounds. Paste text or an article URL, choose a TTS backend and voice, and
the app narrates it over a random clip of your gameplay footage with captions
burned in.

---

## Screenshots

<details>
  <summary><i>Click to show screenshots</i></summary>

![Generate](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_5.17.25_PM.png)
![Link](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.14.47_PM.png)
![Progress Bar](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.11.06_PM.png)
![Browse](https://teb.codes/2-Code/Docker/Subway-Surfers/Screenshot_2025-07-12_at_9.29.02_PM.png)

</details>

## 🆕 What's New in v1.3.0

- **🔌 Pluggable TTS backends** — choose **TikTok** (free, no key), **ElevenLabs**
  (API key), or a **Remote** TTS server (run your own generator elsewhere).
  Selectable via the `TTS_BACKEND` env var **and** a per-video dropdown in the
  UI, with the voice list updating to match the chosen backend.
- **🐛 Fixed startup crash** (issue #2: `ModuleNotFoundError: new_pipeline`).
- **💬 Real captions restored** — word-by-word captions are burned in with
  ffmpeg's subtitle renderer (no OpenCV/MoviePy). Timing is estimated from the
  text by default, or taken from an optional Whisper ASR server for word-accuracy.
- **🔒 Hardened & cleaned up** — replaced `os.system`/bash scripts with
  `subprocess` argument lists (no shell, no injection surface, runs on Windows
  too), re-enabled text cleaning, and removed dead modules (Vosk, OpenCV) and
  unused dependencies for a much smaller image.

*Full history in [version.py](version.py).*

## ✨ Features

- **Text or URL input** — article URLs are auto-extracted (goose3).
- **Three TTS backends**, selectable per video:
  | Backend | Key required | Notes |
  |---|---|---|
  | `tiktok` | none | Free public TikTok voices (default) |
  | `elevenlabs` | `ELEVENLABS_API_KEY` | High-quality voices from your account |
  | `remote` | none | Delegate to your own TTS server (`REMOTE_TTS_URL`) |
- **Word-by-word burned captions**, TikTok-style, centered with outline.
- **Adjustable speed** (0.25×–3×) and random gameplay segment selection.
- **Real-time progress** over Server-Sent Events.
- **Video management page** — browse, view, download and delete generated videos.

## 🚀 Quick Start

### Docker (recommended)

```bash
# Default (free TikTok voices). Mount a folder of .mp4 gameplay clips.
docker run -p 5000:5000 \
  -v /path/to/gameplay:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# ElevenLabs backend
docker run -p 5000:5000 \
  -e TTS_BACKEND=elevenlabs -e ELEVENLABS_API_KEY=sk_... \
  -v /path/to/gameplay:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Remote TTS backend
docker run -p 5000:5000 \
  -e TTS_BACKEND=remote -e REMOTE_TTS_URL=http://my-tts-server:8080 \
  -v /path/to/gameplay:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

Or with Compose (see [docker-compose.yml](docker-compose.yml)):

```bash
mkdir gameplay   # drop your .mp4 clips here
docker compose up
# Optional accurate caption timing:
# docker compose --profile whisper up   (then set WHISPER_ASR_URL=http://whisper-asr:9000)
```

Open **http://localhost:5000**.

### Local development

```bash
git clone https://github.com/tebwritescode/subwaysurfers-text-multi.git
cd subwaysurfers-text-multi
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements-pip.txt   # requires the system `ffmpeg` binary on PATH
cp .env.example .env                  # edit as needed
# add at least one .mp4 gameplay clip to ./static/
python app.py
```

## 🔧 Configuration

All configuration is via environment variables (a local `.env` file is
supported). See [.env.example](.env.example).

| Variable | Default | Description |
|---|---|---|
| `TTS_BACKEND` | `tiktok` | Default backend: `tiktok`, `elevenlabs`, or `remote` |
| `ELEVENLABS_API_KEY` | – | API key for the ElevenLabs backend |
| `REMOTE_TTS_URL` | – | Remote TTS server: `POST {text, voice}` → audio bytes |
| `REMOTE_TTS_VOICES_URL` | `${REMOTE_TTS_URL}/voices` | Remote backend voice list endpoint |
| `WHISPER_ASR_URL` | – | Optional whisper-asr-webservice for accurate caption timing |
| `CAPTION_TIMING_OFFSET` | `0.0` | Seconds to show captions earlier |
| `CAPTION_FONT` | `DejaVu Sans` | Caption font (must be available to ffmpeg/libass) |
| `SOURCE_VIDEO_DIR` | `static` | Directory of gameplay `.mp4` clips, or a single file |
| `PORT` | `5000` | Web server port |

## 🏗️ Architecture

```
subwaysurfers-text-multi/
├── app.py              # Flask routes, SSE progress, /api/voices
├── sub.py              # Pipeline orchestrator (text → sections → clips → final)
├── content.py          # URL article extraction
├── cleantext.py        # TTS-safe text cleaning
├── text_splitter.py    # Long-text sectioning
├── text_to_speech.py   # TTS backend dispatcher
├── tiktokvoice.py      # TikTok TTS backend
├── elevenlabs_tts.py   # ElevenLabs TTS backend
├── remote_tts.py       # Remote TTS backend
├── captions.py         # Word timing + ASS subtitle generation
├── video_compose.py    # ffmpeg: gameplay + captions + audio → mp4
├── templates/          # index / progress / output / videos / viewtext
├── static/             # gameplay .mp4 clips + styles.css
└── final_videos/       # generated videos
```

**Tech stack:** Python 3.13 · Flask · ffmpeg (libass for captions) · goose3 · pydub.

## 🔐 Security

- Input/URL validation on all submissions.
- No shell usage: external tools are invoked via `subprocess` argument lists.
- Sanitized output filenames; process isolation in Docker.
- CodeQL `security-extended` analysis runs in CI.

## 🛠️ Development

```bash
python -m pytest test_app.py        # offline unit tests
# Multi-arch image (CI does this automatically on push to main):
docker buildx build --platform linux/amd64,linux/arm64 \
  -t tebwritescode/subwaysurfers-text20:latest --push .
```

## 📝 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgments

- TikTok TTS relay projects, ElevenLabs, and `openai-whisper-asr-webservice`
- FFmpeg / libass for rendering
- The open-source community

---

**Created by**: [tebbydog0605](https://github.com/tebbydog0605)
**Docker Hub**: [tebwritescode](https://hub.docker.com/u/tebwritescode)
**Website**: [teb.codes](https://teb.codes)

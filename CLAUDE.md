# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Task Management

Claude Code maintains a todo list to track tasks and progress. The todo list is managed in memory during each session and includes:
- Pending tasks to be implemented
- Tasks currently in progress
- Completed tasks from the current session

Key todo list guidelines:
- Always push to the `dev` branch until functionality is verified
- Increment the patch version (third number) for each build/test cycle
- Never push to main branch or update dockerhub latest tag without explicit instruction
- General code cleanup tasks should be deferred until specifically requested

## Overview

This is a Flask web application that converts article links or text into engaging Subway Surfers-style videos with text-to-speech narration. The application extracts text from URLs, generates speech using TikTok voices, creates synchronized captions, and overlays them on gameplay footage.

## Essential Setup

Before running the application, ensure these prerequisites are met:

1. **Vosk English Model**: Download from https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip and extract to `static/vosk-model-en-us-0.22/`
2. **Background Video**: Place at least one `.mp4` file (e.g., `surf.mp4`) in the `static/` directory
3. **Python Environment**: Use Python 3.11 or 3.12

## Automated CI/CD

### GitHub Actions Workflows

**Docker Build & Push** (`.github/workflows/docker-build.yml`):
- ✅ **Trigger**: Every push to `main` branch
- ✅ **Multi-Architecture**: Supports AMD64 and ARM64
- ✅ **Auto-Versioning**: Uses version from `version.py` 
- ✅ **Docker Hub**: Pushes to `tebwritescode/subwaysurfers-text20`
- ✅ **Tags**: Creates both versioned tag (e.g., `v1.1.16`) and `latest`

**CodeQL Security Analysis** (`.github/workflows/codeql.yml`):
- ✅ **Trigger**: Push to `main`, PRs, and weekly schedule
- ✅ **Security Scans**: Advanced security and quality queries
- ✅ **Vulnerability Detection**: Automated security issue reporting

### Required GitHub Secrets

For automated Docker builds to work, ensure these secrets are set in GitHub repository settings:
- `DOCKER_USERNAME`: Your Docker Hub username 
- `DOCKER_PASSWORD`: Your Docker Hub password/token

## Common Commands

### Development Server
```bash
# Standard development server
flask run

# Custom port with all interfaces (use with caution)
flask run -h 0.0.0.0 -p 3000
```

### Environment Setup
```bash
# Create virtual environment
python3.12 -m venv .venv

# Activate environment
source ./.venv/bin/activate

# Install dependencies
pip3 install -r requirements-pip.txt
```

### Docker Commands
```bash
# Build image
docker build -t subwaysurfers-text .

# Run container
docker run -p 5000:5000 subwaysurfers-text
```

## Architecture

### Core Workflow

1. **app.py**: Main Flask application handling routes and form submission
   - `/` - Home page with input form
   - `/submit-form` - Processes text/URL and triggers video generation
   - `/output` - Displays generated video with streaming support

2. **sub.py**: Orchestrates the video generation pipeline
   - Validates inputs and dependencies
   - Coordinates text extraction, speech synthesis, caption generation, and video assembly
   - Handles error propagation back to Flask

3. **Processing Pipeline**:
   - **cleantext.py**: Extracts and cleans text from URLs using goose3
   - **text_to_speech.py**: Generates speech using TikTok voices API
   - **timestamper.py**: Creates word-level timestamps using Vosk speech recognition
   - **videomaker.py**: Generates caption overlays using OpenCV
   - **concat.sh**: Combines video and audio using FFmpeg

### Key Dependencies

- **Flask**: Web framework
- **goose3**: Article text extraction
- **vosk**: Speech recognition for timestamp generation
- **opencv-python**: Video processing and caption rendering
- **moviepy**: Video editing
- **FFmpeg**: Video/audio multiplexing (via shell scripts)

### File Structure

- `static/`: Contains CSS, background videos, and Vosk model
- `templates/`: HTML templates for web interface
- `final_videos/`: Output directory for generated videos
- Generated files use timestamp-based naming: `{timestamp}_speed{speed}_voice{voice}_final.mp4`

## Important Notes

- The application requires significant disk space for video processing
- FFmpeg must be installed system-wide (handled in Docker, manual for local dev)
- Video generation can be CPU-intensive and time-consuming
- The concat.sh script includes commented NVIDIA GPU acceleration options
- All generated videos include both the .mp4 file and corresponding .txt file with source text

## Development Guidelines

- **Branch Management**:
  - Always push to the dev branch until functionality is verified
  - Never push to other branches or overwrite the latest flag in dockerhub unless specifically instructed

- **Version Control**:
  - Increment the Minor Version number by one for each set of changes
  - Use a global, user-unmodifiable version variable for tracking version numbers

- **Project Management**:
  - Maintain a local todo list 
  - Document the todo list location
  - Update with tasks that need fixing and those that have been resolved
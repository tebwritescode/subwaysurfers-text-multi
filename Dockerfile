# Subway Surfers Text-to-Video Generator
# Python 3.13 slim base. Video composition and caption burning use the system
# ffmpeg binary (with libass), so no Python video libraries are needed.

FROM python:3.13-slim

WORKDIR /app

# System dependencies:
#  - ffmpeg: audio/video processing + caption burning (libass)
#  - fonts-dejavu-core: provides "DejaVu Sans" so libass can render captions
#  - build toolchain + headers: lets any sdist-only deps build on arm64
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-dejavu-core \
    curl \
    gcc \
    g++ \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

ENV FLASK_APP=app.py \
    DOCKER_ENV=true \
    PYTHONUNBUFFERED=1 \
    TTS_BACKEND=tiktok

# Install Python dependencies first for better layer caching.
COPY requirements-docker.txt .
RUN pip install --no-cache-dir --upgrade pip --break-system-packages --root-user-action=ignore && \
    pip install --no-cache-dir -r requirements-docker.txt --break-system-packages --root-user-action=ignore

# Copy the application.
COPY . /app

# Generated videos directory (typically mounted as a volume).
RUN mkdir -p /app/final_videos && chmod 755 /app/final_videos

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:5000/ || exit 1

CMD ["python", "app.py"]

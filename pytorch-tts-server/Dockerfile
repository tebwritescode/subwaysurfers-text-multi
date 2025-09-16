# Multi-stage build for optimized PyTorch TTS Server Docker Image
# Serves Bark TTS models with CPU and GPU support

# Stage 1: Builder for dependencies
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    cmake \
    libffi-dev \
    libsndfile1-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
WORKDIR /build
COPY requirements.txt .

# Install PyTorch CPU version by default (smaller image)
# For GPU, override with --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cu118
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install --upgrade pip setuptools wheel && \
    pip install torch torchaudio --index-url ${TORCH_INDEX_URL} && \
    pip install -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    # PyTorch optimizations
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4 \
    NUMEXPR_NUM_THREADS=4 \
    # Model cache directories
    TRANSFORMERS_CACHE=/app/cache \
    HF_HOME=/app/models \
    TORCH_HOME=/app/models/torch

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    curl \
    espeak-ng \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash ttsuser && \
    mkdir -p /app/models /app/cache /app/temp /app/voices && \
    chown -R ttsuser:ttsuser /app

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=ttsuser:ttsuser . .

# Ensure scripts are executable
RUN chmod +x /app/start.sh

# Switch to non-root user
USER ttsuser

# Create volume mount points
VOLUME ["/app/models", "/app/cache", "/app/voices"]

# Expose port
EXPOSE 8000

# Health check with proper timeout for model loading
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - can be overridden for mock server
CMD ["./start.sh"]
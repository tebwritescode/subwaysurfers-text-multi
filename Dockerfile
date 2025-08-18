# Use official Python image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install minimal system dependencies for Python packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    gcc \
    g++ \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for WhisperASR integration
ENV WHISPER_ASR_URL=http://host.docker.internal:9000
ENV FLASK_APP=app.py
ENV DOCKER_ENV=true

# Copy necessary files to /app
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip --break-system-packages --root-user-action=ignore
RUN pip install -r requirements-docker.txt --break-system-packages --root-user-action=ignore

# Create directories for generated videos and ensure proper permissions
RUN mkdir -p /app/final_videos && \
    chmod 755 /app/final_videos

# Expose the Flask application's default port
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]
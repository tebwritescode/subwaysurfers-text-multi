# Use official Python image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies required for Homebrew
RUN apt-get update && apt-get install -y \
    curl \
    git \
    sudo \
    procps \
    build-essential \
    python3-dev \
    libffi-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# # Install Homebrew
# RUN /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
#     && echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> /root/.bashrc \
#     && eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# # Set Homebrew path
# ENV PATH="/home/linuxbrew/.linuxbrew/bin:${PATH}"

# Copy necessary files to /app
COPY . /app

# Upgrade pip, setuptools, and wheel before installing dependencies
RUN pip install --upgrade pip setuptools wheel --break-system-packages

# Install required Python dependencies
RUN pip install -r requirements-pip.txt --break-system-packages

# Install Homebrew dependencies
# RUN if [ -f requirements-brew.txt ]; then cat requirements-brew.txt | xargs brew install; fi

# Ensure the Vosk English Model is available in the `/app/static` directory
# RUN wget -O vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip && \
#     mkdir -p /app/static/vosk-model && \
#     unzip vosk-model.zip -d /app/static/ && \
#     rm vosk-model.zip

# Expose the Flask application's default port
EXPOSE 5000

# Start the Flask application
CMD ["flask", "run", "--host=0.0.0.0"]
# Text to Tracks: A Subway Surfers Video Article Converter

## Inspiration
Remaining focused and attentive when reading educational materials can often be difficult. Recognizing this challenge, we set out to create a solution that makes learning more captivating and enjoyable.

## What It Does
Our web application transforms article links by extracting the text and presenting it in a Subway Surfers-style video format akin to TikTok. This engaging format allows users to absorb information more effectively by capturing their attention.

## How We Built It
The application was constructed using a combination of Python, HTML/CSS, Flask, OpenCV, goose3, Vosk API, among other Python libraries.

## Supported Platforms
The project was tested on macOS and the local server is compatible with Safari, Chrome, and Firefox browsers.

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

## Installation

1. Ensure [Python](https://www.python.org/) (Tested on version 3.11 and 3.12) is installed on your system.

2. Clone the repository and change into that directory using the following commands:
   ```
   git clone https://github.com/tebwritescode/subwaysurfers-text-multi.git
   cd subwaysurfers-text-multi
   ```

3. Set up a Python environment using version 3.12.
   ```
   python3.12 -m venv .venv
   ```
4. Activate the new python environment.
   ```
   source ./.venv/bin/activate
   ```
5. Install the required `pip3` dependencies:
   ```
   pip3 install -r requirements-pip.txt
   ```

6. Download the Subway Surfers [background gameplay](https://drive.google.com/file/d/1ZyFZKIB1HiZM_XDQPRRiiAIvU4sgl10k/view?usp=drive_link), rename it to `surf.mp4`, and place it into the `static` folder of your local repository. Additional videos can be added to the `./static` folder, and one will be randomly selected for each run.

7. Obtain the [Vosk English Model](https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip), unzip it, and place the folder into the `static` directory of your local repository.

8. Start the development server with:
   ```
   flask run
   ```

or

8. Start the development server opening all interfaces and selecting a custom port(HERE BE DRAGONS, know the danger) replace 3000 with your port of choice
   ```
   flask run -h 0.0.0.0 -p 3000
   ```

9. In your browser, access the local server.

10. Paste the article link you wish to convert into the text box and click `Submit`. While video generation may take some time, the terminal will indicate the program is functioning. If prompted to override any files, proceed to override them.

## Running with Docker

### Quick Start
```bash
# Using a directory of videos (random selection)
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e CAPTION_TIMING_OFFSET=-0.1 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest

# Using a specific video file
docker run -p 5000:5000 \
  -e WHISPER_ASR_URL=http://your-whisper-server:9000 \
  -e SOURCE_VIDEO_DIR=/app/static/surf.mp4 \
  -v /path/to/videos:/app/static \
  tebwritescode/subwaysurfers-text20:latest
```

### Docker Hub
https://hub.docker.com/r/tebwritescode/subwaysurfers-text20

### Environment Variables

The Docker container accepts the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_ASR_URL` | `http://host.docker.internal:9000` | URL of the WhisperASR server for speech-to-text caption timing synchronization |
| `PORT` | `5000` | Port number for the Flask web server |
| `CAPTION_TIMING_OFFSET` | `0.0` | Timing offset in seconds for caption display (negative values show captions earlier) |
| `MODEL_PATH` | `static/vosk-model-en-us-0.22` | Path to the Vosk speech recognition model |
| `SOURCE_VIDEO_DIR` | `static` | Path to a video file or directory. If a file, uses that specific video. If a directory, randomly selects from available videos |
| `FLASK_APP` | `app.py` | Flask application entry point |
| `DOCKER_ENV` | `true` | Indicates the application is running in a Docker container |

### Volume Mounts

Mount your video files to `/app/static` to make them available to the application:
```bash
-v /path/to/your/videos:/app/static
```

## Planned Features
- Offloading transcoding to a separate container to allow transcoding on a different server
- Dropdown to select source video
- Allow uploading source videos from web client

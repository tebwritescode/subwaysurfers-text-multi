# SubwaySurfers with ElevenLabs TTS Integration

This is a modified version of the SubwaySurfers video generator that replaces TikTok TTS with ElevenLabs AI voices.

## Features

- **ElevenLabs TTS Integration**: High-quality AI voices with 24+ voice options
- **Python 3.13 Compatible**: Updated for latest Python with audioop-lts support
- **Docker Support**: Ready for containerized deployment
- **Automatic Video Generation**: Combines gameplay footage with AI narration

## Prerequisites

- Python 3.13+
- FFmpeg
- ElevenLabs API key

## Installation

### Local Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd subwaysurfers
```

2. Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements-pip.txt
pip install audioop-lts  # For Python 3.13 compatibility
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ElevenLabs API key
```

5. Add source video:
```bash
# Place at least one .mp4 file in the static/ directory
```

6. Run the application:
```bash
python app.py
```

Access the application at http://localhost:5000

### Docker Setup

1. Build the image:
```bash
docker build -t subwaysurfers-elevenlabs:latest .
```

2. Run the container:
```bash
docker run -d \
  -p 5000:5000 \
  -e ELEVENLABS_API_KEY="your_api_key_here" \
  -v $(pwd)/final_videos:/app/final_videos \
  subwaysurfers-elevenlabs:latest
```

## Configuration

### Environment Variables

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (required)
- `FLASK_APP`: Flask application file (default: app.py)
- `MODEL_PATH`: Path to Vosk model (not needed for ElevenLabs)

### Available Voices

The application supports 24+ ElevenLabs voices including:
- Rachel, Clyde, Roger, Sarah, Laura
- Thomas, Charlie, George, Callum, River
- Harry, Liam, Alice, Matilda, Will
- Jessica, Eric, Chris, Brian, Daniel
- Lily, Bill, Bateman, Edward

## Usage

1. Navigate to the web interface
2. Enter text or article URL
3. Select an ElevenLabs voice
4. Adjust playback speed if needed
5. Click Submit to generate video
6. Download the generated video with AI narration

## API Integration

The application uses the ElevenLabs Python SDK:

```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
audio = client.generate(
    text="Your text here",
    voice="voice_id",
    model="eleven_monolingual_v1"
)
```

## Python 3.13 Compatibility

This version addresses Python 3.13 changes:
- `audioop` module removal: Fixed with `audioop-lts` package
- `aifc` module removal: Replaced with `pydub` for audio duration

## Changes from Original

- Replaced TikTok TTS with ElevenLabs API
- Added `elevenlabs_tts.py` module
- Updated `text_to_speech.py` to use ElevenLabs
- Modified UI to show ElevenLabs voices
- Fixed Python 3.13 compatibility issues
- Removed Vosk model dependency for ElevenLabs workflow

## Troubleshooting

### Missing API Key
Ensure `ELEVENLABS_API_KEY` is set in your environment or `.env` file

### Python 3.13 Issues
Install `audioop-lts` package: `pip install audioop-lts`

### No Source Videos
Place at least one `.mp4` file in the `static/` directory

### Docker Build Issues
Ensure Docker Desktop is running and you have sufficient disk space

## License

Based on the original SubwaySurfers project. Modified for ElevenLabs integration.

## Credits

- Original SubwaySurfers project: [tebwritescode/subwaysurfers-text-multi](https://github.com/tebwritescode/subwaysurfers-text-multi)
- ElevenLabs API: [elevenlabs.io](https://elevenlabs.io)
- Modified with Claude Code assistance
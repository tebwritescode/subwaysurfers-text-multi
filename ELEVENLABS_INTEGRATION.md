# ElevenLabs TTS Integration Guide

## Overview
This guide explains how to integrate ElevenLabs Text-to-Speech (TTS) into the Subway Surfers Text-to-Video Generator alongside existing TikTok TTS and Bark TTS options.

## Why ElevenLabs?

ElevenLabs offers:
- **Ultra-realistic voices** - Industry-leading voice synthesis quality
- **Voice cloning** - Create custom voices from audio samples
- **Multilingual support** - 29+ languages with natural accents
- **Emotional control** - Fine-tune voice emotions and speaking styles
- **Low latency** - Fast synthesis suitable for real-time applications
- **Professional quality** - Studio-grade audio output

## Prerequisites

### 1. ElevenLabs Account
Sign up at [elevenlabs.io](https://elevenlabs.io) and obtain your API key:
1. Create an account (free tier available)
2. Navigate to Profile Settings → API Keys
3. Copy your API key

### 2. Install Dependencies
```bash
pip install elevenlabs
```

## Integration Steps

### Step 1: Add ElevenLabs Configuration

Add to your environment variables (`.env` file):
```bash
# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL  # Default voice (Sarah)
ELEVENLABS_MODEL=eleven_turbo_v2  # or eleven_monolingual_v1
ELEVENLABS_ENABLED=true
```

### Step 2: Create ElevenLabs TTS Module

Create `elevenlabs_tts.py`:
```python
import os
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech integration"""

    # Popular voice IDs
    VOICES = {
        "sarah": "EXAVITQu4vr4xnSDxMaL",
        "rachel": "21m00Tcm4TlvDq8ikWAM",
        "bella": "pFZP5JQG7iQjIQuC4Prp",
        "antoni": "ErXwobaYiN019PkySvjV",
        "elli": "MF3mGyEYCl7XYWbV9V6O",
        "josh": "TxGEqnHWrfWFTfGW9XjX",
        "arnold": "VR6AewLTigWG4xSOukaG",
        "adam": "pNInz6obpgDQGcFmaJgB",
        "sam": "yoZ06aMxZJJ28mfd3POQ",
    }

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2")
        self.enabled = os.getenv("ELEVENLABS_ENABLED", "false").lower() == "true"

        if self.enabled and not self.api_key:
            logger.warning("ElevenLabs enabled but no API key provided")
            self.enabled = False

    def synthesize(
        self,
        text: str,
        voice: str = "sarah",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> Optional[bytes]:
        """
        Synthesize text to speech using ElevenLabs

        Args:
            text: Text to synthesize
            voice: Voice name or ID
            stability: Voice stability (0-1, higher = more consistent)
            similarity_boost: Voice clarity (0-1, higher = clearer)
            style: Style exaggeration (0-1, for v2 models only)
            use_speaker_boost: Enhance speaker similarity

        Returns:
            Audio bytes in MP3 format, or None if failed
        """
        if not self.enabled:
            logger.info("ElevenLabs not enabled, skipping synthesis")
            return None

        # Get voice ID
        voice_id = self.VOICES.get(voice.lower(), voice)

        # Prepare request
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": use_speaker_boost
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            logger.info(f"Successfully synthesized {len(text)} characters with ElevenLabs")
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            return None

    def get_voices(self) -> Optional[Dict[str, Any]]:
        """Get list of available voices"""
        if not self.enabled:
            return None

        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch voices: {e}")
            return None

    def clone_voice(
        self,
        name: str,
        files: list,
        description: str = ""
    ) -> Optional[str]:
        """
        Clone a voice from audio samples

        Args:
            name: Name for the cloned voice
            files: List of audio file paths (mp3/wav)
            description: Voice description

        Returns:
            Voice ID if successful, None otherwise
        """
        if not self.enabled:
            return None

        url = f"{self.base_url}/voices/add"
        headers = {"xi-api-key": self.api_key}

        data = {
            "name": name,
            "description": description
        }

        files_data = []
        for file_path in files:
            with open(file_path, 'rb') as f:
                files_data.append(('files', f))

        try:
            response = requests.post(
                url,
                data=data,
                files=files_data,
                headers=headers
            )
            response.raise_for_status()

            voice_data = response.json()
            logger.info(f"Successfully cloned voice: {voice_data['voice_id']}")
            return voice_data['voice_id']

        except requests.exceptions.RequestException as e:
            logger.error(f"Voice cloning failed: {e}")
            return None
```

### Step 3: Update Main TTS Module

Update `text_to_speech.py` to include ElevenLabs:

```python
from elevenlabs_tts import ElevenLabsTTS

class TextToSpeech:
    def __init__(self):
        # ... existing code ...
        self.elevenlabs = ElevenLabsTTS()

    def synthesize(self, text, voice="sarah", tts_provider="auto"):
        """
        Synthesize text with specified provider

        Priority order (if auto):
        1. ElevenLabs (if enabled and API key present)
        2. Bark TTS (if server running)
        3. TikTok TTS (fallback)
        """

        # Try ElevenLabs first if enabled
        if tts_provider in ["elevenlabs", "auto"] and self.elevenlabs.enabled:
            audio = self.elevenlabs.synthesize(text, voice)
            if audio:
                # Save to file
                output_path = f"temp_audio/elevenlabs_{voice}.mp3"
                with open(output_path, 'wb') as f:
                    f.write(audio)
                return output_path

        # Fall back to Bark or TikTok
        # ... existing fallback code ...
```

### Step 4: Add UI Support

Update `templates/index.html`:

```html
<!-- TTS Provider Selection -->
<div class="form-group">
    <label for="tts_provider">TTS Provider:</label>
    <select id="tts_provider" name="tts_provider">
        <option value="auto">Auto (Best Available)</option>
        <option value="elevenlabs">ElevenLabs (Premium)</option>
        <option value="bark">Bark (High Quality)</option>
        <option value="tiktok">TikTok (Fast)</option>
    </select>
</div>

<!-- Voice Selection (updates based on provider) -->
<div class="form-group">
    <label for="voice">Voice:</label>
    <select id="voice" name="voice">
        <!-- ElevenLabs voices -->
        <optgroup label="ElevenLabs">
            <option value="sarah">Sarah (Female, Young)</option>
            <option value="rachel">Rachel (Female, Mature)</option>
            <option value="bella">Bella (Female, Soft)</option>
            <option value="josh">Josh (Male, Young)</option>
            <option value="adam">Adam (Male, Deep)</option>
            <option value="arnold">Arnold (Male, Mature)</option>
        </optgroup>
        <!-- Bark voices -->
        <optgroup label="Bark TTS">
            <option value="narrator">Narrator</option>
            <option value="announcer">Announcer</option>
            <option value="excited">Excited</option>
        </optgroup>
        <!-- TikTok voices -->
        <optgroup label="TikTok">
            <option value="en_us_001">English US Female</option>
            <option value="en_uk_001">English UK Male</option>
        </optgroup>
    </select>
</div>
```

## Usage Examples

### Basic Usage
```python
from elevenlabs_tts import ElevenLabsTTS

# Initialize
tts = ElevenLabsTTS()

# Generate speech
audio_bytes = tts.synthesize(
    text="Welcome to the future of text-to-speech!",
    voice="sarah",
    stability=0.5,
    similarity_boost=0.75
)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```

### Voice Cloning
```python
# Clone a custom voice
voice_id = tts.clone_voice(
    name="CustomVoice",
    files=["sample1.mp3", "sample2.mp3"],
    description="My custom voice"
)

# Use cloned voice
audio = tts.synthesize("Hello from my custom voice!", voice=voice_id)
```

### Integration with Video Pipeline
```python
# In your video generation pipeline
def generate_video_with_elevenlabs(text, voice="sarah"):
    # 1. Generate audio with ElevenLabs
    audio_path = elevenlabs.synthesize(text, voice)

    # 2. Get timestamps from WhisperASR
    timestamps = get_word_timestamps(audio_path)

    # 3. Generate video with captions
    video_path = create_video_with_captions(
        audio_path,
        timestamps,
        background_video="subway_surfers.mp4"
    )

    return video_path
```

## Docker Configuration

Add to `docker-compose.yml`:

```yaml
services:
  app:
    environment:
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - ELEVENLABS_VOICE_ID=${ELEVENLABS_VOICE_ID}
      - ELEVENLABS_MODEL=${ELEVENLABS_MODEL}
      - ELEVENLABS_ENABLED=${ELEVENLABS_ENABLED}
```

## Cost Optimization

### Free Tier Limits
- 10,000 characters/month
- 3 custom voices
- Standard quality

### Optimization Tips
1. **Cache generated audio** - Reuse for identical text
2. **Batch processing** - Combine short texts
3. **Use turbo model** - Faster and cheaper for most use cases
4. **Implement fallback** - Switch to Bark/TikTok when quota exceeded

### Cost Calculation
```python
def calculate_cost(text_length, tier="starter"):
    """Calculate ElevenLabs cost"""
    rates = {
        "free": {"chars": 10000, "cost": 0},
        "starter": {"chars": 30000, "cost": 5},
        "creator": {"chars": 100000, "cost": 22},
        "pro": {"chars": 500000, "cost": 99}
    }

    tier_info = rates[tier]
    chars_per_dollar = tier_info["chars"] / max(tier_info["cost"], 1)
    estimated_cost = text_length / chars_per_dollar

    return estimated_cost
```

## Comparison Table

| Feature | ElevenLabs | Bark TTS | TikTok TTS |
|---------|------------|----------|------------|
| **Quality** | Ultra-realistic | High | Good |
| **Speed** | Fast (1-2s) | Slow (10-30s) | Very Fast (<1s) |
| **Voices** | 100+ & Custom | 5 presets | 20+ |
| **Languages** | 29+ | English | 10+ |
| **Cost** | $5-99/month | Free | Free |
| **Voice Cloning** | Yes | No | No |
| **Emotion Control** | Yes | Limited | No |
| **API Limits** | Tier-based | None | Rate limited |
| **Audio Format** | MP3/PCM | WAV | MP3 |
| **Latency** | 100-500ms | 5-30s | 50-200ms |

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   ```bash
   export ELEVENLABS_API_KEY="your_actual_key"
   ```

2. **Quota Exceeded**
   - Check usage at elevenlabs.io/speech-synthesis
   - Implement fallback to Bark/TikTok
   - Consider upgrading plan

3. **Voice Not Found**
   ```python
   # List available voices
   voices = tts.get_voices()
   for voice in voices['voices']:
       print(f"{voice['name']}: {voice['voice_id']}")
   ```

4. **Audio Format Issues**
   - ElevenLabs returns MP3 by default
   - Convert if needed: `ffmpeg -i input.mp3 output.wav`

## Advanced Features

### Multilingual Support
```python
# Spanish with native accent
audio = tts.synthesize(
    text="Hola, ¿cómo estás?",
    voice="spanish_voice_id",
    model="eleven_multilingual_v2"
)
```

### Streaming Response
```python
# For real-time applications
def stream_synthesis(text, voice):
    url = f"{base_url}/text-to-speech/{voice}/stream"
    # ... streaming implementation
```

### Voice Fine-tuning
```python
# Adjust voice parameters for different moods
styles = {
    "calm": {"stability": 0.8, "similarity_boost": 0.5},
    "excited": {"stability": 0.3, "similarity_boost": 0.9},
    "serious": {"stability": 0.7, "similarity_boost": 0.7}
}

audio = tts.synthesize(text, **styles["excited"])
```

## Security Best Practices

1. **Never commit API keys**
   ```bash
   # .gitignore
   .env
   *_api_key*
   ```

2. **Use environment variables**
   ```python
   api_key = os.getenv("ELEVENLABS_API_KEY")
   ```

3. **Implement rate limiting**
   ```python
   from functools import lru_cache
   import hashlib

   @lru_cache(maxsize=100)
   def cached_synthesis(text_hash, voice):
       # Cache by text hash to avoid re-synthesis
       pass
   ```

4. **Monitor usage**
   ```python
   def track_usage(text):
       char_count = len(text)
       # Log to monitoring service
       logger.info(f"ElevenLabs usage: {char_count} characters")
   ```

## Testing

### Unit Tests
```python
# test_elevenlabs.py
import unittest
from elevenlabs_tts import ElevenLabsTTS

class TestElevenLabs(unittest.TestCase):
    def setUp(self):
        self.tts = ElevenLabsTTS()

    def test_synthesis(self):
        audio = self.tts.synthesize("Test", voice="sarah")
        self.assertIsNotNone(audio)

    def test_voice_list(self):
        voices = self.tts.get_voices()
        self.assertIn('voices', voices)
```

### Integration Test
```bash
# Test full pipeline with ElevenLabs
curl -X POST http://localhost:5000/generate \
  -d "text=Test ElevenLabs integration" \
  -d "tts_provider=elevenlabs" \
  -d "voice=sarah"
```

## Performance Metrics

Monitor these metrics for optimal performance:
- **Synthesis latency**: Target <500ms
- **Audio quality**: Monitor user feedback
- **API success rate**: Track failures and implement retry
- **Cost per video**: Calculate and optimize
- **Cache hit rate**: Aim for >30% on repeated content

## Migration Path

### From TikTok TTS
1. Set `ELEVENLABS_ENABLED=true`
2. System auto-selects ElevenLabs when available
3. Falls back to TikTok if quota exceeded

### From Bark TTS
1. Map Bark voices to similar ElevenLabs voices
2. Adjust timing offset if needed
3. Update video generation parameters

## Support Resources

- **Documentation**: [elevenlabs.io/docs](https://elevenlabs.io/docs)
- **API Reference**: [api.elevenlabs.io/docs](https://api.elevenlabs.io/docs)
- **Community**: [discord.gg/elevenlabs](https://discord.gg/elevenlabs)
- **Status Page**: [status.elevenlabs.io](https://status.elevenlabs.io)

## Conclusion

ElevenLabs integration provides professional-grade TTS capabilities with minimal code changes. The system automatically handles provider selection, fallback mechanisms, and error recovery, ensuring reliable video generation regardless of TTS availability.

Start with the free tier to evaluate quality, then scale based on your needs. The modular design allows easy switching between providers without modifying the core video generation pipeline.
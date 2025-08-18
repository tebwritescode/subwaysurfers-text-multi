# Deploy Subway Surfers with Bark TTS on x86_64 Server

## Quick Resume Commands

```bash
# Clone the repository and switch to dev branch
git clone https://github.com/tebwritescode/subwaysurfers-text-multi.git
cd subwaysurfers-text-multi
git checkout dev-bark-tts-integration

# Create required directories
mkdir -p voices models final_videos

# Start the complete stack (AllTalk TTS + Whisper ASR + Main App)
docker-compose -f docker-compose.local-stack.yml up -d

# Monitor the startup (this will take a few minutes for models to download)
docker-compose -f docker-compose.local-stack.yml logs -f

# Check when services are ready
curl http://localhost:7851/api/ready    # AllTalk TTS health check
curl http://localhost:9000/health       # Whisper ASR health check
curl http://localhost:5001              # Main app (should show dynamic voices)
```

## What This Deployment Includes

### 🎛️ **Complete Local Stack**
- **Main App**: http://localhost:5001 - Subway Surfers video generator
- **AllTalk TTS**: http://localhost:7851 - Coqui TTS with XTTS and voice cloning
- **Whisper ASR**: http://localhost:9000 - Local speech-to-text for caption timing
- **TTS WebUI**: http://localhost:7851 - AllTalk web interface for voice management

### 🎙️ **Voice Features**
- Dynamic voice fetching from AllTalk TTS server
- Fallback to TikTok TTS when server unavailable  
- Custom voice directory mounted at `./voices/`
- Support for voice cloning with XTTS
- Bark voice indicators in the web interface

### 🔧 **Key Files**
- `docker-compose.local-stack.yml` - Complete stack orchestration
- `app.py` - Updated with dynamic voice fetching
- `text_to_speech.py` - PyTorch TTS integration with fallback
- `templates/index.html` - Updated UI with TTS system indicators
- `voices/` - Directory for custom voice files
- `LOCAL-STACK.md` - Detailed documentation

## Testing the Integration

```bash
# Test voice fetching
curl http://localhost:5001 | grep -i "bark\|tts"

# Test TTS directly
curl -X POST http://localhost:7851/api/tts-generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test of the TTS system", "voice": "female_1"}'

# Add a custom voice (place .wav file in voices/ directory)
cp your-voice-sample.wav ./voices/morgan_freeman.wav
# Voice should appear in the web interface

# Generate a test video
# Use the web interface at http://localhost:5001
# Select a Bark voice (marked with 🎭)
# Enter test text: "Welcome to Subway Surfers with custom voices!"
```

## Current Status

✅ **Completed Features:**
- Dynamic voice fetching with server detection
- Complete docker-compose stack with all services
- Missing modules restored (new_pipeline, text_splitter, word_aligner)
- Merge conflicts resolved
- Custom voice directory mounting
- Health checks and dependency management

⏳ **Ready for Testing:**
- AllTalk TTS server with XTTS and voice cloning
- Bark voice integration with emoji indicators
- Custom voice file support
- Full video generation pipeline

## Troubleshooting

```bash
# Check container status
docker-compose -f docker-compose.local-stack.yml ps

# View logs for specific service
docker-compose -f docker-compose.local-stack.yml logs alltalk-tts
docker-compose -f docker-compose.local-stack.yml logs whisper-asr
docker-compose -f docker-compose.local-stack.yml logs subway-surfers-app

# Restart specific service
docker-compose -f docker-compose.local-stack.yml restart alltalk-tts

# Clean restart
docker-compose -f docker-compose.local-stack.yml down
docker-compose -f docker-compose.local-stack.yml up -d
```

## Next Steps After Deployment

1. **Download Morgan Freeman Voice**: Add `morgan_freeman.wav` to `./voices/` directory
2. **Test Voice Cloning**: Use AllTalk WebUI at http://localhost:7851
3. **Generate Test Video**: Create a video with custom Bark voice
4. **Monitor Performance**: Check logs for TTS response times
5. **Scale Resources**: Add GPU support if needed (uncomment deploy sections)

---
*Last updated: 2025-08-18*
*Branch: dev-bark-tts-integration*
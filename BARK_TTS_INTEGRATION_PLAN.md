# Bark TTS Integration Implementation Plan

## Project Context
**Repository:** Subway Surfers Text-to-Video Generator
**Current Branch:** `dev-bark-tts-integration`
**Current Version:** v1.1.22
**Status:** ~70% implementation complete, needs testing and optimization

## Project Description
This Flask application generates engaging TikTok-style videos with Subway Surfers gameplay backgrounds, text-to-speech narration, and synchronized captions. The project currently supports TikTok TTS and is adding Bark TTS support for higher quality, more expressive voice synthesis.

## Key Project Files

### Core Application Files
- `app.py` - Main Flask application with routes and video generation
- `sub.py` - Core video generation logic
- `text_to_speech.py` - TTS abstraction layer (supports TikTok and PyTorch TTS)
- `tiktokvoice.py` - TikTok TTS integration
- `whisper_timestamper.py` - WhisperASR timing synchronization
- `videomaker.py` - Video composition and captioning
- `new_pipeline.py` - New video processing pipeline
- `word_aligner.py` - Word alignment for captions

### PyTorch TTS Server (Bark Support)
- `pytorch-tts-server/app.py` - FastAPI server for Bark models
- `pytorch-tts-server/README.md` - Server documentation
- `test-bark-voices.py` - Bark voice testing script

### Configuration Files
- `docker-compose.local-stack.yml` - Local stack configuration
- `requirements-pip.txt` - Python dependencies
- `Dockerfile` - Container configuration

### UI Templates
- `templates/index.html` - Main generation interface
- `templates/videos.html` - Video browser
- `templates/progress.html` - Progress tracking
- `static/styles.css` - Application styles

## Current Implementation Status

### ✅ Completed
- Basic Bark model loading in PyTorch TTS server
- Synthesis endpoint structure
- Voice preset definitions (narrator, announcer, excited, calm, deep)
- Integration hooks in text_to_speech.py
- UI dropdown for voice selection

### ❌ Needs Work
- Complete Bark model initialization with memory optimization
- Test server startup and model loading
- Validate all voice presets work correctly
- Full end-to-end video generation with Bark
- Error handling and TikTok TTS fallback
- Memory profiling and optimization
- Progress indicators for Bark loading
- Documentation updates

## CRITICAL EXECUTION INSTRUCTIONS

### Project Management Rules
1. **@agent-bitchy-code-boss is the PROJECT MANAGER**
   - ONLY this agent can check off todo items
   - Verifies completion before marking done
   - Monitors for circular issues (max 3 iterations per todo)
   - Ensures server runs 2 minutes without errors after each todo

2. **Version Control Protocol**
   - Create local commits after each phase
   - Run `git status` and `git diff` before commits
   - If stuck >3 iterations, rollback with `git reset --hard HEAD~1`
   - Try different approach after rollback

3. **Testing Requirements**
   - Start server and monitor for 2 minutes after each major change
   - Use `python app.py` and check for errors
   - Test with `python test-bark-voices.py` for Bark functionality
   - Generate test videos to verify full pipeline

## Detailed Todo List with Agent Assignments

### Phase 1: Testing & Validation (CRITICAL - Start Here)

#### Todo 1: Test PyTorch TTS Server Startup
**Agent:** `qa-engineer-bug-hunter`
**MCP Tools:** Bash, Read, Grep
**Actions:**
1. Read `pytorch-tts-server/app.py` to understand startup
2. Start server: `cd pytorch-tts-server && python app.py`
3. Test health endpoint: `curl http://localhost:8000/health`
4. Check for Bark model loading in logs
**Verification:** Server starts, health endpoint responds, no errors

#### Todo 2: Run Bark Voice Tests
**Agent:** `qa-engineer-bug-hunter`
**MCP Tools:** Bash, Read
**Actions:**
1. Review `test-bark-voices.py` script
2. Ensure PyTorch TTS server is running
3. Execute: `python test-bark-voices.py`
4. Check `voice_samples/` directory for generated audio
**Verification:** All voice presets generate .wav files successfully

#### Todo 3: Fix Any Issues Found
**Agent:** `backend-developer-python`
**MCP Tools:** Edit, MultiEdit, Read
**Actions:**
1. Fix any errors from todos 1-2
2. Update `pytorch-tts-server/app.py` if needed
3. Update `text_to_speech.py` integration if needed
**Verification:** Previous tests now pass

#### Todo 4: Generate Full Test Video
**Agent:** `qa-engineer-bug-hunter`
**MCP Tools:** Bash, Read
**Actions:**
1. Start main Flask app: `python app.py`
2. Use curl or browser to generate video with Bark voice
3. Check `final_videos/` for output
4. Verify audio and captions are synchronized
**Verification:** Complete video with Bark narration works

### Phase 2: Error Handling & Stability

#### Todo 5: Test Error Handling
**Agent:** `qa-engineer-bug-hunter`
**MCP Tools:** Bash, Read, Edit
**Actions:**
1. Stop PyTorch TTS server
2. Try generating video (should fallback to TikTok TTS)
3. Test with invalid voice names
4. Test with very long text
**Verification:** Graceful fallback without crashes

#### Todo 6: Implement Robust Fallback
**Agent:** `backend-developer-python`
**MCP Tools:** Edit, MultiEdit
**Actions:**
1. Update `text_to_speech.py` fallback logic
2. Add try-catch blocks for Bark failures
3. Implement health check before using Bark
**Verification:** Automatic fallback to TikTok TTS when Bark unavailable

### Phase 3: Performance Optimization

#### Todo 7: Profile Memory Usage
**Agent:** `system-architect-performance`
**MCP Tools:** Bash, Read
**Actions:**
1. Add memory profiling to `pytorch-tts-server/app.py`
2. Monitor memory during Bark model loading
3. Test with multiple sequential requests
4. Document memory requirements
**Verification:** Memory usage documented, no leaks found

#### Todo 8: Optimize Model Caching
**Agent:** `system-architect-performance`
**MCP Tools:** Edit, MultiEdit
**Actions:**
1. Implement model singleton in PyTorch TTS server
2. Add model preloading on server start
3. Optimize model cleanup between requests
**Verification:** Reduced loading time on subsequent requests

#### Todo 9: Add Progress Indicators
**Agent:** `frontend-developer-modernizer`
**MCP Tools:** Edit, Read
**Actions:**
1. Update `templates/index.html` for Bark loading status
2. Add JavaScript progress updates
3. Update `static/styles.css` for loading animations
**Verification:** Users see clear loading feedback

### Phase 4: Documentation & Deployment

#### Todo 10: Update README
**Agent:** `technical-writer-documentation`
**MCP Tools:** Edit, Read
**Actions:**
1. Add Bark TTS section to README.md
2. Document environment variables for Bark
3. Add Bark voice options list
4. Include troubleshooting section
**Verification:** Clear Bark setup instructions in README

#### Todo 11: Configure Docker
**Agent:** `devops-engineer-docker`
**MCP Tools:** Edit, Read
**Actions:**
1. Update `docker-compose.local-stack.yml` for Bark service
2. Set proper memory limits for Bark container
3. Configure volume mounts for models
4. Test Docker deployment
**Verification:** Bark works in Docker environment

#### Todo 12: Create Deployment Guide
**Agent:** `technical-writer-documentation`
**MCP Tools:** Write
**Actions:**
1. Create `BARK-DEPLOYMENT.md`
2. Document production setup steps
3. Include performance tuning tips
4. Add monitoring recommendations
**Verification:** Complete deployment guide exists

### Phase 5: Final Testing Suite

#### Todo 13: End-to-End Integration Test
**Agent:** `qa-engineer-bug-hunter`
**MCP Tools:** Bash, Read
**Actions:**
1. Test all Bark voices with sample texts
2. Generate videos of various lengths
3. Test with different text sources (URL vs direct)
4. Verify caption synchronization
**Verification:** All features work seamlessly

#### Todo 14: Extended Stability Test
**Agent:** `qa-engineer-bug-hunter`
**MCP Tools:** Bash, BashOutput
**Actions:**
1. Start server with: `python app.py`
2. Let run for 2+ minutes
3. Monitor logs for errors
4. Check memory usage over time
**Verification:** No crashes or memory leaks

#### Todo 15: Final Commit and Documentation
**Agent:** `bitchy-code-boss`
**MCP Tools:** Bash, TodoWrite
**Actions:**
1. Review all changes with `git status`
2. Create final commit with all Bark integration
3. Update version.py to v1.1.23
4. Verify all todos completed
**Verification:** Clean commit with working Bark TTS

## Environment Variables

```bash
# PyTorch TTS Server (Bark)
PYTORCH_TTS_ENDPOINT=http://localhost:8000
PYTORCH_TTS_MODEL=suno/bark

# Main Application
WHISPER_ASR_URL=http://localhost:9000
CAPTION_TIMING_OFFSET=-0.1
SOURCE_VIDEO_DIR=./static
FLASK_PORT=5000
```

## Testing Commands

```bash
# Start PyTorch TTS server
cd pytorch-tts-server && python app.py

# Test Bark voices
python test-bark-voices.py

# Start main Flask app
python app.py

# Generate test video with Bark
curl -X POST http://localhost:5000/generate \
  -d "article=Test text for Bark TTS" \
  -d "voice=narrator"

# Check server health
curl http://localhost:8000/health
```

## Success Criteria
- ✅ PyTorch TTS server starts without errors
- ✅ All Bark voice presets generate audio
- ✅ Full videos generate with Bark narration
- ✅ Fallback to TikTok TTS works when needed
- ✅ Memory usage within acceptable limits (<4GB)
- ✅ Documentation complete and accurate
- ✅ Docker deployment configured
- ✅ Server runs stable for 2+ minutes

## Known Issues & Risks
1. **Large Model Size**: Bark models are ~5GB, may cause memory issues
2. **Slow Initial Load**: First model load takes 30-60 seconds
3. **GPU vs CPU**: Performance varies significantly
4. **Memory Leaks**: Monitor for gradual memory increase

## How to Start Implementation

When ready to begin, tell the assistant:
**"Begin implementing the Bark TTS integration plan from BARK_TTS_INTEGRATION_PLAN.md using agent-bitchy-code-boss as project manager"**

This will:
1. Load this plan
2. Start bitchy-code-boss as project manager
3. Begin with Phase 1 testing
4. Systematically work through all todos
5. Ensure proper testing and commits

## Important Notes
- DO NOT skip testing phases
- DO NOT mark todos complete without verification
- DO NOT proceed if server crashes
- DO commit after each successful phase
- DO rollback if stuck after 3 attempts
# version.py
# Global version configuration for Subway Surfers Text-to-Video Generator
# Version format: MAJOR.MINOR.PATCH
# - MAJOR: Major redesigns and features
# - MINOR: Features being added
# - PATCH: Steps during troubleshooting, testing and modifications

__version__ = "1.1.20"

# Version history:
# 1.0.0 - Initial versioning system implementation (based on Docker image v20)
# 1.0.1 - Added version display to web interface
# 1.0.2 - Fixed video file not found error, improved error handling and logging
# 1.0.3 - Added error handling for long texts and text extraction failures
# 1.0.4 - Added version display to all template pages
# 1.0.5 - Docker build with comprehensive bug fixes and improvements
# 1.0.6 - Fixed overlapping captions issue, added extensive video generation logging
# 1.0.7 - Implemented real-time progress tracking with Server-Sent Events
# 1.0.8 - Proportional progress tracking and app crash resilience
# 1.0.9 - Fixed TTS hanging on complex/long texts, improved text preprocessing
# 1.0.10 - Implemented multi-section processing for long texts, removed text truncation, dynamic progress tracking
# 1.0.11 - Fixed corrupted output file in source video directory, improved file path handling
# 1.0.12 - Disabled video frame progress updates to fix caption timing drift issues
# 1.0.13 - Fixed timestamp-to-frame conversion using round() instead of int() truncation
# 1.1.0 - Major fix: Use original text for captions with STT timing alignment (fixes mismatched captions)
# 1.1.1 - Clean text once at pipeline start to ensure consistency between TTS and captions
# 1.1.2 - TESTING: Disabled cleantext to isolate timing issues, re-enabled progress bars
# 1.1.3 - TESTING: Disabled word alignment, using STT words directly like original version
# 1.1.14 - FIXED: Restored WhisperASR pipeline for perfect caption timing synchronization
# 1.1.15 - TIMING: Added 0.25s timing offset to show captions before words are spoken
# 1.1.16 - CONFIG: Made caption timing offset configurable via CAPTION_TIMING_OFFSET environment variable
# 1.1.17 - DOCKER: Fixed Docker build by removing problematic dependencies with fallbacks
# 1.1.18 - DOCKER: Fixed build by using Python 3.12 and complete original requirements per README
# 1.1.19 - FIXED: Restored proper pydub import and PYDUB_AVAILABLE variable definition
# 1.1.20 - FIXED: Updated CodeQL workflow to use v3 (v2 deprecated), resolved SARIF processing issues
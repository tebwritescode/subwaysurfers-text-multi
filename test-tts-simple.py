#!/usr/bin/env python3
"""
Simple TTS integration test
"""
import os
import sys

# Set environment variables
os.environ['PYTORCH_TTS_ENDPOINT'] = 'http://localhost:8000'
os.environ['PYTORCH_TTS_MODEL'] = 'suno/bark'

# Test PyTorch TTS client directly
from pytorch_tts import PyTorchTTSClient, tts

def test_client():
    print("Testing PyTorch TTS Client")
    print("=" * 40)

    client = PyTorchTTSClient("http://localhost:8000")

    # Test health check
    if client.health_check():
        print("✅ Server is healthy")
    else:
        print("❌ Server not responding")
        return False

    # Test synthesis
    text = "Hello from Subway Surfers with Bark TTS!"
    audio_bytes = client.synthesize(text, "narrator", "suno/bark")

    if audio_bytes:
        print(f"✅ Synthesis successful ({len(audio_bytes)} bytes)")

        # Save to file
        with open("test_output.wav", "wb") as f:
            f.write(audio_bytes)
        print("✅ Saved to test_output.wav")
    else:
        print("❌ Synthesis failed")
        return False

    # Test tts function
    if tts(text, "excited", "test_excited.wav"):
        print("✅ TTS function works (test_excited.wav)")
    else:
        print("❌ TTS function failed")
        return False

    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    success = test_client()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Bark Voice Testing Script
Tests different Bark voices with sample text
"""
import requests
import json
import base64
import os
import time
from pathlib import Path

# Configuration
PYTORCH_TTS_URL = "http://localhost:8000"
OUTPUT_DIR = Path("./voice_samples")
OUTPUT_DIR.mkdir(exist_ok=True)

# Test phrases for different voice characteristics
TEST_PHRASES = {
    "narrator": "Welcome to Subway Surfers! In this thrilling endless runner game, you'll dash through subway tunnels, avoiding trains and collecting coins.",
    "announcer": "Ladies and gentlemen, presenting the most exciting mobile game of the year - Subway Surfers!",
    "excited": "Oh my goodness! This is absolutely incredible! The graphics are amazing and the gameplay is so smooth!",
    "calm": "Take a moment to appreciate the beautiful art style and smooth animations in this well-crafted mobile experience.",
    "deep": "From the depths of the underground subway system comes a game that will challenge your reflexes and test your skills."
}

def test_server_health():
    """Check if the PyTorch TTS server is running"""
    try:
        response = requests.get(f"{PYTORCH_TTS_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ PyTorch TTS Server is healthy")
            print(f"   Device: {response.json().get('device', 'unknown')}")
            return True
        else:
            print(f"❌ Server unhealthy: {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def get_available_voices():
    """Get list of available voices"""
    try:
        response = requests.get(f"{PYTORCH_TTS_URL}/voices")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Available voices: {len(data['voices'])}")
            print(f"   Recommended: {data.get('recommended', [])}")
            return data['voices']
        else:
            print(f"❌ Failed to get voices: {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"❌ Error getting voices: {e}")
        return []

def synthesize_voice(text, voice, model="suno/bark"):
    """Synthesize speech for a specific voice"""
    payload = {
        "text": text,
        "voice": voice, 
        "model": model,
        "language": "en"
    }
    
    try:
        print(f"   Synthesizing with {voice}...")
        start_time = time.time()
        
        response = requests.post(
            f"{PYTORCH_TTS_URL}/synthesize",
            json=payload,
            timeout=120  # Bark can take time to load
        )
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # Save audio file
                audio_b64 = data["audio_data"]
                audio_bytes = base64.b64decode(audio_b64)
                
                filename = OUTPUT_DIR / f"{voice}_sample.wav"
                with open(filename, "wb") as f:
                    f.write(audio_bytes)
                
                print(f"   ✅ {voice}: {duration:.1f}s generation, {data.get('duration', 0):.1f}s audio")
                return True
            else:
                print(f"   ❌ {voice}: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ {voice}: HTTP {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"   ❌ {voice}: {e}")
        return False

def test_voice_batch():
    """Test multiple voices using the batch endpoint"""
    try:
        print("\n🎤 Testing voice batch endpoint...")
        response = requests.post(
            f"{PYTORCH_TTS_URL}/test-voices",
            timeout=300  # 5 minutes for multiple voices
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data["results"]
            
            print(f"   Test text: '{data['test_text']}'")
            print(f"   Voices tested: {len(results)}")
            
            for voice, result in results.items():
                if result["success"]:
                    # Save batch test audio
                    audio_b64 = result["audio_data"]
                    audio_bytes = base64.b64decode(audio_b64)
                    
                    filename = OUTPUT_DIR / f"batch_{voice}_test.wav"
                    with open(filename, "wb") as f:
                        f.write(audio_bytes)
                    
                    print(f"   ✅ {voice}: {result['duration']:.1f}s")
                else:
                    print(f"   ❌ {voice}: {result['error']}")
            
            return True
        else:
            print(f"   ❌ Batch test failed: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"   ❌ Batch test error: {e}")
        return False

def main():
    """Main testing function"""
    print("🎮 Bark Voice Testing for Subway Surfers")
    print("=" * 50)
    
    # Check server health
    if not test_server_health():
        print("\n❌ Server not available. Make sure to run:")
        print("   docker-compose -f docker-compose.local-stack.yml up pytorch-tts")
        return
    
    # Get available voices
    voices = get_available_voices()
    if not voices:
        return
    
    print(f"\n🔊 Output directory: {OUTPUT_DIR.absolute()}")
    
    # Test individual voices with custom phrases
    print(f"\n🎯 Testing individual voices...")
    success_count = 0
    
    for voice in ["narrator", "announcer", "excited", "calm", "deep"]:
        if voice in voices:
            text = TEST_PHRASES.get(voice, "This is a test of the Bark text to speech system.")
            if synthesize_voice(text, voice):
                success_count += 1
    
    # Test batch endpoint
    if test_voice_batch():
        print("\n✅ Batch testing completed")
    
    # Summary
    print(f"\n📊 Results Summary:")
    print(f"   Individual tests: {success_count}/5 succeeded")
    print(f"   Audio files saved to: {OUTPUT_DIR.absolute()}")
    
    if success_count > 0:
        print(f"\n🎧 Listen to the generated samples:")
        for file in OUTPUT_DIR.glob("*.wav"):
            print(f"   {file.name}")
        
        print(f"\n🚀 Ready to use with Subway Surfers!")
        print(f"   Set PYTORCH_TTS_ENDPOINT=http://localhost:8000")
        print(f"   Set PYTORCH_TTS_MODEL=suno/bark")
    else:
        print(f"\n❌ No voices generated successfully. Check server logs.")

if __name__ == "__main__":
    main()
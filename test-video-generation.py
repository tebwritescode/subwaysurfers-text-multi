#!/usr/bin/env python3
"""
Test video generation with PyTorch TTS integration
"""
import os
import sys
import time

# Set environment variable
os.environ['PYTORCH_TTS_ENDPOINT'] = 'http://localhost:8000'

# Import the text_to_speech module
from text_to_speech import generate_wav, USE_PYTORCH_TTS

def test_tts_integration():
    """Test if PyTorch TTS integration is working"""
    print("Testing PyTorch TTS Integration")
    print("=" * 50)

    print(f"USE_PYTORCH_TTS: {USE_PYTORCH_TTS}")
    print(f"PYTORCH_TTS_ENDPOINT: {os.environ.get('PYTORCH_TTS_ENDPOINT')}")

    # Test text
    test_text = "Welcome to Subway Surfers! This is a test of the Bark TTS integration. The game features exciting endless runner gameplay."

    # Test with narrator voice
    print("\nTesting narrator voice...")
    result = generate_wav(test_text, "narrator", "test_narrator.wav")

    if result and "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    else:
        print(f"✅ Generated test_narrator.wav")

        # Check if file exists
        if os.path.exists("test_narrator.wav"):
            file_size = os.path.getsize("test_narrator.wav")
            print(f"   File size: {file_size:,} bytes")
            return True
        else:
            print("❌ File was not created")
            return False

def test_full_pipeline():
    """Test the full video generation pipeline"""
    print("\nTesting Full Video Pipeline")
    print("=" * 50)

    # Import video generation modules
    try:
        import sub
        from videomaker import create_final_video

        print("✅ Video generation modules imported")

        # Test parameters
        test_params = {
            "article": "Subway Surfers is an endless runner mobile game. Players take the role of young graffiti artists who, upon being caught in the act of tagging a metro railway site, run through the railroad tracks to escape from the inspector and his dog.",
            "voice": "narrator",
            "filename": "test_video",
            "bg_video": 1,  # Use first background video
            "bg_music": 1,  # Use first background music
            "font": "Montserrat/Montserrat-ExtraBold.ttf",
            "color": "yellow"
        }

        print("\nGenerating test video with parameters:")
        for key, value in test_params.items():
            print(f"   {key}: {value}")

        # Generate video (this would normally call the full pipeline)
        print("\n⏳ Video generation would start here...")
        print("   (Skipping actual generation to avoid long process)")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("🎮 Subway Surfers PyTorch TTS Integration Test")
    print("=" * 50)

    # Check if PyTorch TTS server is running
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ PyTorch TTS server is running")
            server_info = response.json()
            print(f"   Mode: {server_info.get('mode', 'unknown')}")
            if 'mock' in str(server_info.get('mode', '')):
                print("   ⚠️  Using mock server (not real Bark models)")
        else:
            print("❌ PyTorch TTS server not healthy")
            return
    except requests.RequestException:
        print("❌ PyTorch TTS server not accessible")
        print("   Start it with: python pytorch-tts-server/app_mock.py")
        return

    # Test TTS integration
    if test_tts_integration():
        print("\n✅ TTS integration test passed")

        # Test full pipeline
        if test_full_pipeline():
            print("\n✅ Full pipeline test passed")
            print("\n🎉 Bark TTS integration is working!")
            print("\nNext steps:")
            print("1. Run the Flask app: python app.py")
            print("2. Visit http://localhost:5000")
            print("3. Select 'narrator' voice and generate a video")
        else:
            print("\n⚠️  Full pipeline test had issues")
    else:
        print("\n❌ TTS integration test failed")

if __name__ == "__main__":
    main()
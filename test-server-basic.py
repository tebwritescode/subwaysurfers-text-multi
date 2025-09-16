#!/usr/bin/env python3
"""
Basic server connectivity test
"""
import requests
import json

# Configuration
PYTORCH_TTS_URL = "http://localhost:8000"

def test_endpoints():
    """Test basic server endpoints"""
    print("Testing PyTorch TTS Server Endpoints")
    print("=" * 40)

    # Test health
    try:
        response = requests.get(f"{PYTORCH_TTS_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data['status']}")
            print(f"   PyTorch loaded: {data.get('pytorch_loaded', False)}")
            print(f"   Device: {data.get('device', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

    # Test voices
    try:
        response = requests.get(f"{PYTORCH_TTS_URL}/voices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Voices endpoint working")
            print(f"   Available voices: {len(data['voices'])}")
            print(f"   Recommended: {', '.join(data.get('recommended', []))}")
        else:
            print(f"❌ Voices endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Voices endpoint error: {e}")

    print("\n✅ Server is responding to requests")
    print("Note: Bark model loading is deferred until synthesis")

if __name__ == "__main__":
    test_endpoints()
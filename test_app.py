#!/usr/bin/env python3
"""
Simple test application to demonstrate ElevenLabs integration
"""

from flask import Flask, render_template, jsonify
from elevenlabs_tts import get_elevenlabs_voices
import os

app = Flask(__name__)

@app.route('/')
def home():
    """Test page showing ElevenLabs integration status"""
    try:
        voices_result = get_elevenlabs_voices()
        elevenlabs_voices = voices_result.get("voices", [])
        elevenlabs_error = voices_result.get("error", None)
    except Exception as e:
        elevenlabs_voices = []
        elevenlabs_error = str(e)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SubwaySurfers ElevenLabs Integration Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
            .voice-list {{ margin: 20px 0; }}
            .voice-item {{ margin: 5px 0; padding: 5px; background: #f0f0f0; }}
        </style>
    </head>
    <body>
        <h1>SubwaySurfers ElevenLabs Integration Test</h1>

        <h2>Integration Status:</h2>
        {"<p class='error'>❌ " + elevenlabs_error + "</p>" if elevenlabs_error else "<p class='success'>✅ ElevenLabs API connection successful!</p>"}

        <h2>Available Voices:</h2>
        <div class="voice-list">
            {"".join([f"<div class='voice-item'>🎤 {voice['name']} (ID: {voice['id']})</div>" for voice in elevenlabs_voices]) if elevenlabs_voices else "<p>No voices available</p>"}
        </div>

        <h2>Environment:</h2>
        <p>ELEVENLABS_API_KEY configured: {'✅ Yes' if os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_API_KEY') != 'your_elevenlabs_api_key_here' else '❌ No'}</p>

        <h2>Next Steps:</h2>
        <ol>
            <li>Add your ElevenLabs API key to the .env file</li>
            <li>Install missing dependencies for full video generation pipeline</li>
            <li>Test video generation with ElevenLabs voices</li>
        </ol>
    </body>
    </html>
    """

@app.route('/api/voices')
def api_voices():
    """API endpoint for voices"""
    try:
        return get_elevenlabs_voices()
    except Exception as e:
        return {"voices": [], "error": str(e)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
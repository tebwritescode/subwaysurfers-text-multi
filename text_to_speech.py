import os
# TTS system selection with fallback logic
PYTORCH_TTS_ENDPOINT = os.getenv('PYTORCH_TTS_ENDPOINT')

if PYTORCH_TTS_ENDPOINT:
    # Use external PyTorch TTS server if configured
    try:
        from pytorch_tts import tts, PyTorchTTSClient
        # Test if server is available
        client = PyTorchTTSClient(PYTORCH_TTS_ENDPOINT)
        if not client.health_check():
            print(f"Warning: PyTorch TTS server at {PYTORCH_TTS_ENDPOINT} is not responding, falling back to TikTok TTS")
            from tiktokvoice import tts
            USE_PYTORCH_TTS = False
        else:
            USE_PYTORCH_TTS = True
    except ImportError:
        print("Warning: pytorch_tts module not found, falling back to TikTok TTS")
        from tiktokvoice import tts
        USE_PYTORCH_TTS = False
else:
    # Default to TikTok TTS
    from tiktokvoice import tts
    USE_PYTORCH_TTS = False
from pydub import AudioSegment
from goose3 import Goose
from cleantext import cleantext
import os, audioread, subprocess
import validators

# Pydub should be available since it's in requirements
PYDUB_AVAILABLE = True

def generate_wav(article, voice, output_file):
    """
    Generate a WAV audio file from text or article URL using text-to-speech.
    
    This function takes either a direct text input or a URL to an article,
    converts the text to speech using TikTok's voice synthesis, and saves
    the result as a WAV file.
    
    Args:
        article (str): Either a URL to an article or direct text content
        voice (str): The voice ID to use for text-to-speech synthesis
        output_file (str): Path where the output WAV file will be saved
    
    Returns:
        dict: {"error": "error message"} if failed, {} if successful
    
    Note:
        - If article is a valid URL, the function will extract the article text using Goose
        - The function first creates an MP3 file and then converts it to WAV format
    """
    try:
        g = Goose()
        # Check if the input is a URL
        if validators.url(article):
            # If it's a URL, extract text using Goose
            try:
                extracted_article = g.extract(article)
                text = extracted_article.cleaned_text
                if not text or len(text.strip()) == 0:
                    return {"error": "No text content could be extracted from the URL"}
            except Exception as e:
                return {"error": f"Failed to extract text from URL: {str(e)}"}
        else:
            # If it's not a URL, assume it's direct text
            text = cleantext(article)
        
        # Check text length
        if len(text) == 0:
            return {"error": "No text content to process"}
        
        # No text length limit - sections will be handled by the caller
            
        # Additional text cleaning for TTS
        text = text.strip()
        if not text:
            return {"error": "No readable text content after processing"}
            
        # Generate TTS and save as audio with timeout
        try:
            import signal
            import threading
            
            tts_result = {"error": None, "completed": False}
            
            def tts_worker():
                try:
                    if USE_PYTORCH_TTS:
                        # Use PyTorch TTS with potential custom models
                        model = os.getenv('PYTORCH_TTS_MODEL', 'microsoft/speecht5_tts')
                        speaker_embedding = os.getenv('SPEAKER_EMBEDDING_PATH')
                        
                        # Check if voice is a path to audio file for cloning
                        if voice.endswith(('.wav', '.mp3', '.flac')) and os.path.exists(voice):
                            # Voice cloning mode - output directly to MP3 isn't supported, use WAV first
                            tts(text, voice, "output.wav", pytorch_endpoint=PYTORCH_TTS_ENDPOINT, model=model)
                            
                            # Convert WAV to MP3 for compatibility
                            if os.path.exists("output.wav"):
                                sound = AudioSegment.from_wav("output.wav")
                                sound.export("output.mp3", format="mp3")
                        else:
                            # Standard synthesis - check if model supports MP3 output
                            try:
                                # Try direct MP3 output first
                                tts(text, voice, "output.mp3", pytorch_endpoint=PYTORCH_TTS_ENDPOINT, 
                                    model=model, speaker_embedding=speaker_embedding)
                            except:
                                # Fallback to WAV then convert
                                tts(text, voice, "output.wav", pytorch_endpoint=PYTORCH_TTS_ENDPOINT,
                                    model=model, speaker_embedding=speaker_embedding)
                                
                                if os.path.exists("output.wav"):
                                    sound = AudioSegment.from_wav("output.wav")
                                    sound.export("output.mp3", format="mp3")
                    else:
                        # Use TikTok TTS
                        tts(text, voice, "output.mp3")
                    
                    tts_result["completed"] = True
                except Exception as e:
                    tts_result["error"] = str(e)
            
            # Start TTS in a separate thread with timeout
            thread = threading.Thread(target=tts_worker)
            thread.daemon = True
            thread.start()
            # Longer timeout for PyTorch TTS which may be slower
            timeout = 120 if USE_PYTORCH_TTS else 60
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                return {"error": "Text-to-speech generation timed out. Text may be too complex."}
            
            if tts_result["error"]:
                return {"error": f"Text-to-speech generation failed: {tts_result['error']}"}
                
            if not tts_result["completed"]:
                return {"error": "Text-to-speech generation did not complete"}
                
        except Exception as e:
            return {"error": f"Text-to-speech generation failed: {str(e)}"}
        
        # Verify MP3 was created
        if not os.path.exists("output.mp3"):
            return {"error": "TTS output file was not created"}
            
        # Convert MP3 to WAV format
        try:
            if PYDUB_AVAILABLE:
                sound = AudioSegment.from_mp3("output.mp3")
                sound.export(output_file, format="wav")
            else:
                # Use FFmpeg directly when pydub is not available
                ffmpeg_cmd = ["ffmpeg", "-i", "output.mp3", "-y", output_file]
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return {"error": f"FFmpeg conversion failed: {result.stderr}"}
        except Exception as e:
            return {"error": f"Audio format conversion failed: {str(e)}"}
            
        return {}  # Success
        
    except Exception as e:
        return {"error": f"Unexpected error in generate_wav: {str(e)}"}

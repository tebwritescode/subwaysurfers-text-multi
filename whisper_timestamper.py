import requests
import json
import os
import logging

logger = logging.getLogger(__name__)

def get_words_and_timestamps_whisper(audio_file_path, whisper_server_url=None):
    """
    Generate word-level timestamps using YOUR Whisper ASR server ONLY
    
    Args:
        audio_file_path (str): Path to the audio file
        whisper_server_url (str): URL to your existing Whisper server (optional)
                                 If not provided, will use WHISPER_ASR_URL env var
    
    Returns:
        tuple: (words_list, timestamps_list)
    
    Raises:
        Exception: If Whisper ASR server is unreachable or fails
    """
    
    # Use environment variable if no URL provided
    if not whisper_server_url:
        whisper_server_url = os.getenv('WHISPER_ASR_URL', 'http://whisper-asr:9000')
    
    logger.info(f"ONLY using YOUR Whisper ASR server: {whisper_server_url}")
    logger.info("No fallbacks - will fail if server is unreachable")
    
    return _get_timestamps_from_server(audio_file_path, whisper_server_url)

def _get_timestamps_from_server(audio_file_path, server_url):
    """
    Get timestamps from your existing Whisper server
    """
    try:
        logger.info(f"Connecting to Whisper server at {server_url}")
        
        # Prepare the audio file for upload
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio_file': audio_file}  # onerahmet uses 'audio_file' parameter
            
            # onerahmet/openai-whisper-asr-webservice API format
            # Send as query parameters, not form data
            params = {
                'task': 'transcribe',
                'language': 'en',
                'word_timestamps': 'true',
                'output': 'json'
            }
            
            # onerahmet/openai-whisper-asr-webservice uses /asr endpoint
            endpoint = f"{server_url}/asr"
            
            logger.info(f"Trying endpoint: {endpoint}")
            response = requests.post(
                endpoint,
                files=files,
                params=params,  # Use params for query parameters
                timeout=300  # 5 minute timeout for long audio
            )
            
            if response.status_code == 200:
                result = response.json()
                return _extract_words_from_whisper_response(result)
            else:
                logger.error(f"Whisper server error: {response.status_code} - {response.text}")
                raise Exception(f"Whisper server failed with status {response.status_code}")
                
    except Exception as e:
        logger.error(f"Failed to connect to Whisper ASR server at {server_url}: {e}")
        raise Exception(f"Whisper ASR server connection failed: {e}")  # Don't fall back, fail properly

def _get_timestamps_local_whisper(audio_file_path):
    """
    Get timestamps using local Whisper installation
    """
    try:
        import whisper
        logger.info("Using local Whisper for transcription with word timestamps")
        
        # Load Whisper model (you can change to 'large' for better accuracy)
        model = whisper.load_model("base")
        
        # Transcribe with word-level timestamps
        result = model.transcribe(
            audio_file_path,
            word_timestamps=True,
            language="en"
        )
        
        return _extract_words_from_whisper_response(result)
        
    except ImportError:
        logger.error("Whisper not installed. Install with: pip install openai-whisper")
        raise Exception("Neither Whisper server nor local Whisper available")
    except Exception as e:
        logger.error(f"Local Whisper failed: {e}")
        raise

def _extract_words_from_whisper_response(whisper_result):
    """
    Extract words and timestamps from Whisper response
    
    faster-whisper can return different formats:
    1. Standard format: {"segments": [{"words": [...]}]}
    2. Direct format: {"words": [...]}
    3. Text + words: {"text": "...", "words": [...]}
    """
    words = []
    timestamps = []
    
    try:
        logger.info(f"Processing Whisper response: {json.dumps(whisper_result, indent=2)[:500]}...")
        
        # Try direct words format first (faster-whisper sometimes uses this)
        if 'words' in whisper_result:
            for word_info in whisper_result['words']:
                word = word_info.get('word', '').strip()
                start_time = word_info.get('start', 0)
                
                if word:  # Skip empty words
                    words.append(word)
                    timestamps.append(start_time)
        
        # Try standard segments format
        elif 'segments' in whisper_result:
            for segment in whisper_result['segments']:
                if 'words' in segment:
                    for word_info in segment['words']:
                        word = word_info.get('word', '').strip()
                        start_time = word_info.get('start', 0)
                        
                        if word:  # Skip empty words
                            words.append(word)
                            timestamps.append(start_time)
        
        # If no words found, try to extract from text (fallback)
        elif 'text' in whisper_result and not words:
            logger.warning("No word-level timestamps found, falling back to text splitting")
            text = whisper_result['text']
            text_words = text.split()
            # Create fake timestamps (this is not ideal but better than failing)
            for i, word in enumerate(text_words):
                words.append(word)
                timestamps.append(i * 0.5)  # Assume 0.5s per word as fallback
        
        logger.info(f"Extracted {len(words)} words with Whisper timestamps")
        logger.info(f"First 10 words: {words[:10]}")
        logger.info(f"First 10 timestamps: {timestamps[:10]}")
        
        return words, timestamps
        
    except Exception as e:
        logger.error(f"Failed to extract words from Whisper response: {e}")
        logger.error(f"Response structure: {json.dumps(whisper_result, indent=2) if isinstance(whisper_result, dict) else str(whisper_result)}")
        raise

def test_whisper_connection(server_url=None):
    """
    Test connection to Whisper server or local installation
    """
    if server_url:
        try:
            response = requests.get(f"{server_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    else:
        try:
            import whisper
            return True
        except ImportError:
            return False
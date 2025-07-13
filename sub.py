from videomaker import create_video
from timestamper import get_words_and_timestamps
from text_to_speech import generate_wav
import subprocess
import ffmpeg
import os
import audioread
import time
import random
import logging
import sys
import traceback
import validators

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

"""
CONSTANTS AND CONFIGURATION
"""
MODEL_PATH = "static/vosk-model-en-us-0.22"
SOURCE_VIDEO_DIR = "static"
WAV_FILE = "output.wav"
FAST_WAV_FILE = "output_fast.wav"
MP3_FILE = "output.mp3"
CAPTION_VIDEO = "output_caption.mp4"
PRE_OUTPUT_VIDEO = "output_wrong_encoding.mp4"
OUTPUT_VIDEO = "final.mp4"

"""
FUNCTIONS
"""

def get_random_video(directory=SOURCE_VIDEO_DIR):
    """
    Selects a random video file from the specified directory.

    Args:
        directory (str): Directory path to look for .mp4 files.
    
    Returns:
        str or dict: Path to the randomly chosen video or an error message.
    """
    try:
        if not os.path.isdir(directory):
            return {"error": f"Directory not found: {directory}"}
        
        video_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.lower().endswith('.mp4')]
        if not video_files:
            return {"error": f"No video files found in directory \"{directory}\""}

        return random.choice(video_files)
        # return "static/surf.mp4"  # For testing purposes, return a specific video file
    except Exception as e:
        logger.error(f"Error in get_random_video: {str(e)}")
        logger.debug(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

def verify_vosk_model():
    """
    Checks if the Vosk model directory exists and contains required files.

    Returns:
        dict: {"error": "message"} if model is missing or corrupted, otherwise {}
    """
    if not os.path.exists(MODEL_PATH):
        return {"error": f"Missing Vosk model directory: \"{MODEL_PATH}\""}

    required_files = ["README", "am", "conf", "graph", "ivector", "rescore", "rnnlm"]
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(MODEL_PATH, f))]
    
    if missing_files:
        return {"error": f"Incomplete Vosk model: Missing \"{MODEL_PATH}/{', '.join(missing_files)}\""}
    
    return {}

def speed_up_audio(input_file, output_file, speed_factor):
    """
    Speeds up an audio file using FFmpeg's atempo filter.

    Parameters:
        input_file (str): Path to the input audio file.
        output_file (str): Path to the output audio file.
        speed_factor (float): Speed factor (e.g., 1.0 for normal speed, 1.5 for 1.5x speed).

    Returns:
        dict: Success message or error description.
    """
    try:
        if speed_factor < 0.5:
            return {"error": "Speed factor too low. Minimum allowed is 0.5x."}

        if not os.path.exists(input_file):
            return {"error": f"Input audio file missing: {input_file}"}

        command = ["ffmpeg", "-i", input_file, "-filter:a", f"atempo={speed_factor}", "-vn", output_file]
        subprocess.run(command, check=True)

        return {"success": f"Audio sped up by {speed_factor}x and saved as {output_file}"}

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error in speed_up_audio: {e}")
        logger.debug(traceback.format_exc())
        return {"error": f"FFmpeg error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in speed_up_audio: {e}")
        logger.debug(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

def validate_text_input(text):
    """Throws an exception if the input contains fewer than 10 words."""
    word_count = len(text.split())  # Count words by splitting on spaces
    if word_count < 10:
        raise ValueError(f"Input contains only {word_count} words. A minimum of 10 is required.")
    return f"Valid input with {word_count} words."

def script(input_text, customspeed, customvoice, final_path="final.mp4"):
    """
    Processes text input and generates a video with captions.

    Args:
        input_text (str): Text to convert to speech.
        customspeed (float): Speech playback speed adjustment.
        customvoice (str): Voice selection for text-to-speech.
        final_path (str): Path to save the final video.

    Returns:
        dict: Success or error message.
    """
    try:
        # ✅ Check if input has at least 10 words
        if not validators.url(input_text):
            logger.info("Text input detected, performing word count validation.")
            word_count = len(input_text.split())
            if word_count < 10:
                raise ValueError("Input text must contain at least 10 words.")
            start = time.time()
        else:
            logger.info("URL detected, skipping word count validation.")

        # ✅ Check if VOSK model exists before using it
        model_check = verify_vosk_model()
        if "error" in model_check:
            return model_check

        # ✅ Get a random video file
        source_video = get_random_video()
        if isinstance(source_video, dict) and "error" in source_video:
            return source_video

        logger.info(f"Source Video Selected: {source_video}")

        logger.info("Cleaning up previous output files...")
        os.system(f"bash clean.sh {OUTPUT_VIDEO}")

        # Remove cleaning of previous final.mp4
        # os.system(f"bash clean.sh {OUTPUT_VIDEO}")

        # Generate TTS audio
        tts_response = generate_wav(input_text, customvoice, WAV_FILE)
        if isinstance(tts_response, dict) and "error" in tts_response:
            return tts_response

        # Adjust playback speed
        speed_response = speed_up_audio(WAV_FILE, FAST_WAV_FILE, customspeed)
        if isinstance(speed_response, dict) and "error" in speed_response:
            return speed_response

        # Extract words and timestamps using dynamic MODEL_PATH
        try:
            texts, timestamps = get_words_and_timestamps(MODEL_PATH, FAST_WAV_FILE)
        except Exception as e:
            return {"error": f"Speech recognition failed due to a model issue: {str(e)}"}

        # Get audio duration
        try:
            sound_duration = int(audioread.audio_open(FAST_WAV_FILE).duration)
        except Exception as e:
            return {"error": f"Failed to determine audio duration: {str(e)}"}

        # Create captioned video
        try:
            create_video(texts, timestamps, sound_duration, source_video, CAPTION_VIDEO)
        except Exception as e:
            return {"error": f"Video creation failed: {str(e)}"}

        # Merge video and audio, output to final_path
        os.system(f"bash concat.sh {CAPTION_VIDEO} {FAST_WAV_FILE} {PRE_OUTPUT_VIDEO} \"{final_path}\"")

        return {"success": "Video generation completed."}

    except Exception as e:
        logger.error(f"Unexpected error in script: {str(e)}")
        logger.debug(traceback.format_exc())
        return {"error": f"Script execution failed: {str(e)}"}

# Test the function when running this script directly
if __name__ == "__main__":
    sample_input = "This is a test sentence."
    print(script(sample_input, 1.0, "en_us_rocket"))

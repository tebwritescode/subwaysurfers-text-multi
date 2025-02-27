from videomaker import create_video
from timestamper import get_words_and_timestamps
from text_to_speech import generate_wav
from compression import compress_video
import subprocess
import ffmpeg, os, audioread
import time
import os
import random

"""
CONSTANTS AND CONFIGURATION
"""
# Path to Vosk model used for word/timestamp processing
MODEL_PATH = "static/vosk-model-en-us-0.22"
# Subway surfers source video
SOURCE_VIDEO = "static/surf.mp4"
# .wav file created by generate_wav() with TTS from article
WAV_FILE = "output.wav"
# .wav file created by speed_up_audio() with adjusted playback speed
FAST_WAV_FILE = "output_fast.wav"
# .mp3 file created by generate_wav() with TTS from article
MP3_FILE = "output.mp3"
# .mp4 file created with captions overlayed on source video
CAPTION_VIDEO = "output_caption.mp4"
# .mp4 file with the wrong encoding (intermediate file)
PRE_OUTPUT_VIDEO = "output_wrong_encoding.mp4"
# Final output video (audio + captioned video)
OUTPUT_VIDEO = "final.mp4"
# Voice used for text-to-speech narration
VOICE = "en_us_006"

"""
FUNCTIONS
"""
def speed_up_audio(input_file, output_file, speed_factor=1.0):
    """
    Speeds up an audio file using FFmpeg's atempo filter.
    
    Parameters:
        input_file (str): Path to the input audio file.
        output_file (str): Path to the output audio file.
        speed_factor (float): Speed factor (e.g., 1.5 for 1.5x speed).
    """
    if speed_factor <= 0:
        print("Error: Speed factor must be greater than 0")
        return
        
    # Constructing the ffmpeg command
    command = [
        "ffmpeg", "-i", input_file, 
        "-filter:a", f"atempo={speed_factor}", 
        "-vn", output_file
    ]
    
    # Run the command
    try:
        subprocess.run(command, check=True)
        print(f"Success: Audio has been sped up by {speed_factor}x and saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def get_random_video(directory='./static'):
    """
    Get a random video file path from the specified directory
    
    Args:
        directory (str): Path to the directory containing video files
    
    Returns:
        str: Full path to a randomly selected video file, or None if no videos found
    """
    try:
        # Ensure the directory exists
        if not os.path.isdir(directory):
            print(f"Error: Directory {directory} does not exist")
            return None
        
        # Find all .mp4 files in the directory
        video_files = [
            os.path.join(directory, f) 
            for f in os.listdir(directory) 
            if f.lower().endswith('.mp4')
        ]
        
        # Check if any video files were found
        if not video_files:
            print(f"No .mp4 files found in {directory}")
            return None
        
        # Select and print a random video file
        random_video = random.choice(video_files)
        print(f"Video file selected: {random_video}")
        
        return random_video
    
    except Exception as e:
        print(f"Error getting random video: {e}")
        return None

def script(input_link, customspeed):
    """
    Main script function that processes text input and generates a video with captions.
    
    Args:
        input_link (str): URL or text content to be processed
        customspeed (float): Speed factor for audio playback
    """
    # Track execution time
    start = time.time()
    
    # Get a random source video
    SOURCE_VIDEO = get_random_video()
    if not SOURCE_VIDEO:
        print("Failed to get a source video. Exiting.")
        return
    else:
        print(f"Source Video File: {SOURCE_VIDEO}")
    
    # Clean up any existing output files
    os.system(f"bash clean.sh {OUTPUT_VIDEO}")
    print("All generated files removed")
    
    # Generate TTS audio from the input text
    generate_wav(input_link, VOICE, WAV_FILE)
    print("Audio file generated.")
    
    # Adjust the audio speed according to user preference
    speed_up_audio(WAV_FILE, FAST_WAV_FILE, customspeed)
    print("Audio sped up.")
    
    # Extract words and their timestamps from the audio
    texts, timestamps = get_words_and_timestamps(MODEL_PATH, FAST_WAV_FILE)
    print("Words and timestamps retrieved.")
    
    # Get the duration of the audio file
    sound_duration = int(audioread.audio_open(FAST_WAV_FILE).duration)
    
    # Create video with captions based on the words and timestamps
    create_video(texts, timestamps, sound_duration, SOURCE_VIDEO, CAPTION_VIDEO)
    print("Captioned video generated.")
    
    # Combine the audio and captioned video into the final output
    os.system(f"bash concat.sh {CAPTION_VIDEO} {FAST_WAV_FILE} {PRE_OUTPUT_VIDEO} {OUTPUT_VIDEO}")
    print("Audio and video combined.")
    
    # Report total processing time
    print("Time to create video: "+str(time.time()-start))

# Execute the script with a sample URL if run directly
if __name__ == '__main__':
    input_link = "https://www.sciencedaily.com/releases/2024/04/240401142454.htm"
    script(input_link, 1.0)

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

VARIABLES

"""

# Path to Vosk model used for word/timestamp processing
MODEL_PATH = "static/vosk-model-en-us-0.22"

# Subway surfers source video
SOURCE_VIDEO = "static/surf.mp4"

# .wav file created by generate_wav() with tts from article
WAV_FILE = "output.wav"

# .wav file created by speed_up_audio()
FAST_WAV_FILE = "output_fast.wav"

# .mp3 file created by generate_wav() with tts from artile
MP3_FILE = "output.mp3"

# .mp4 file created with captions overlayed on subway surfers
CAPTION_VIDEO = "output_caption.mp4"

# .mp4 file with the wrong encoding
PRE_OUTPUT_VIDEO = "output_wrong_encoding.mp4"

# final output video (WAV_FILE + CAPTION_VIDEO)
OUTPUT_VIDEO = "final.mp4"

# voice the article is narrated in
VOICE = "en_us_006"

# Adjust voice read speed
SPEED = 1.7

"""

SCRIPT

"""

def speed_up_audio(input_file, output_file, speed_factor):
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

def script(input_link):
    start = time.time()

    SOURCE_VIDEO = get_random_video()
    if not SOURCE_VIDEO:
        print("Failed to get a source video. Exiting.")
        return
    else:
        print(f"Source Video File: {SOURCE_VIDEO}")

    # removes all old output files and final.mp4
    os.system(f"bash clean.sh {OUTPUT_VIDEO}")
    print("All generated files removed")

    # generated the spoken version of the input article
    generate_wav(input_link, VOICE, WAV_FILE)
    print("Audio file generated.")

    # speed up the audio
    speed_up_audio(WAV_FILE, FAST_WAV_FILE, SPEED)
    print("Audio sped up.")

    # gets the words spoken and their corresponding timestamps from the .wav file
    texts, timestamps = get_words_and_timestamps(MODEL_PATH, FAST_WAV_FILE)
    print("Words and timestamps retrieved.")

    # gets the duration of the .wav file
    sound_duration = int(audioread.audio_open(FAST_WAV_FILE).duration)

    # generates the caption video from the subway surfers source and the words/timestamps
    create_video(texts, timestamps, sound_duration, SOURCE_VIDEO, CAPTION_VIDEO)
    print("Captioned video generated.")

    # combines the sound and the caption video
    os.system(f"bash concat.sh {CAPTION_VIDEO} {FAST_WAV_FILE} {PRE_OUTPUT_VIDEO} {OUTPUT_VIDEO}")
    print("Audio and video combined.")
    print("Time to create video: "+str(time.time()-start))

if __name__ == '__main__':
    input_link = "https://www.sciencedaily.com/releases/2024/04/240401142454.htm"
    script(input_link)

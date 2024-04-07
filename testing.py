from videomaker import create_video
from timestamper import get_words_and_timestamps
from text_to_speech import generate_sound_files
from compression import compress_video
import ffmpeg, os, audioread, time

start_time = time.time()

"""

VARIABLES

"""

# Link to article to be processed
INPUT_LINK = "https://www.sciencedaily.com/releases/2024/04/240401142454.htm"

# Path to Vosk model used for word/timestamp processing
MODEL_PATH = "/Users/danielbonkowsky/Documents/vosk-model-en-us-0.22"

# Subway surfers source video
SOURCE_VIDEO = "static/surf.mp4"

# .wav file created by generate_wav() with tts from article
WAV_FILE = "output.wav"

# .mp3 file created by generate_wav() with tts from artile
MP3_FILE = "output.mp3"

# .mp4 file created with captions overlayed on subway surfers
CAPTION_BIG_VIDEO = "output_caption_big.mp4"

# compressed caption video
CAPTION_SMALL_VIDEO = "output_caption_small.mp4"

# final output video (WAV_FILE + CAPTION_VIDEO)
OUTPUT_VIDEO = "final.mp4"

# voice the article is narrated in
VOICE = "en_us_c3po"

"""

SCRIPT

"""

# removes all old output files and final.mp4
os.system(f"bash clean.sh {OUTPUT_VIDEO}")

# generated the spoken version of the input article
generate_sound_files(INPUT_LINK, VOICE, WAV_FILE)

# gets the words spoken and their corresponding timestamps from the .wav file
texts, timestamps = get_words_and_timestamps(MODEL_PATH, WAV_FILE)

# gets the duration of the .wav file
sound_duration = int(audioread.audio_open(WAV_FILE).duration)

# generates the caption video from the subway surfers source and the words/timestamps
create_video(texts, timestamps, sound_duration, SOURCE_VIDEO, CAPTION_BIG_VIDEO)

compress_video(CAPTION_BIG_VIDEO, CAPTION_SMALL_VIDEO)

# combines the sound and the caption video
os.system(f"bash concat.sh {CAPTION_SMALL_VIDEO} {WAV_FILE} {OUTPUT_VIDEO}")

print(f"Total time: {time.time() - start_time} seconds")
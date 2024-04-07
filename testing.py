from videomaker import create_video
from timestamper import get_words_and_timestamps
from text_to_speech import generate_wav
import ffmpeg, os, audioread

INPUT_LINK = "https://www.sciencedaily.com/releases/2024/04/240401142454.htm"
MODEL_PATH = "/Users/danielbonkowsky/Documents/vosk-model-en-us-0.22"
WAV_FILE = "output.wav"
INPUT_VIDEO = "output_video.mp4"
OUTPUT_VIDEO = "output.mp4"

generate_wav(INPUT_LINK)

get_words_and_timestamps(MODEL_PATH, WAV_FILE)
texts, timestamps = get_words_and_timestamps(MODEL_PATH, WAV_FILE)
sound_duration = int(audioread.audio_open(WAV_FILE).duration)

create_video(texts, timestamps, sound_duration)

os.system(f"bash concat.sh {INPUT_VIDEO} {WAV_FILE} {OUTPUT_VIDEO}")
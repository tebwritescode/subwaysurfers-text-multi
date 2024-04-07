from videomaker import create_video
from vosk_example import get_words_and_timestamps
import ffmpeg, os

INPUT_FILE = "output.wav"

model_path = "/Users/danielbonkowsky/Documents/vosk-model-en-us-0.22"
texts, timestamps = get_words_and_timestamps(model_path, INPUT_FILE)

create_video(texts, timestamps, 532)

input_video = "output_video.mp4"
input_audio = "output.wav"
output_file = "output.mp4"

os.system(f"bash concat.sh {input_video} {input_audio} {output_file}")

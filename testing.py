from videomaker import create_video
from vosk_example import get_words_and_timestamps
import ffmpeg, os


# Array of strings to overlay at different timestamps
texts = ['Text 1', 'Text 2', 'Text 3']
timestamps = [2, 12, 25]  # timestamps

INPUT_FILE = "output.wav"

model_path = "/Users/danielbonkowsky/Documents/vosk-model-en-us-0.22"
texts, timestamps = get_words_and_timestamps(model_path, INPUT_FILE)

create_video(texts, timestamps, 532)

input_video = "output_video.mp4"
input_audio = "output.wav"

os.system("ffmpeg -i output_video.mp4 -i output.wav -c copy -map 0:v:0 -map 1:a:0 output.mp4 -shortest")

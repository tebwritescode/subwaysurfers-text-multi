from tiktokvoice import tts
from pydub import AudioSegment
import os


text = input("Input text to play:: ")
voice = "en_us_006"

# arguments:
#   - input text
#   - vocie which is used for the audio
#   - output file name
#   - play sound after generating the audio
tts(text, voice, "output.mp3", play_sound=False)

sound = AudioSegment.from_mp3("output.mp3")
sound.export("output.wav", format="wav")



from tiktokvoice import tts
import os

text = "My name is"
text2 = "daniel"
voice = "en_us_006"

# arguments:
#   - input text
#   - vocie which is used for the audio
#   - output file name
#   - play sound after generating the audio
tts(text, voice, "output1.mp3", play_sound=False)
tts(text2, voice, "output2.mp3", play_sound=False)

os.system("afplay output1.mp3")
os.system("afplay output2.mp3")
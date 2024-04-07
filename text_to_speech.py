from tiktokvoice import tts
from pydub import AudioSegment
from goose3 import Goose
import os, time

link = input("Input link to article:: ")

start_time = time.time()

g = Goose()
article = g.extract(link)
text = article.cleaned_text

voice = "en_us_006"

#tts(input text, voice, output file, (optional) play sound)
tts(text, voice, "output.mp3")

sound = AudioSegment.from_mp3("output.mp3")
sound.export("output.wav", format="wav")

print(f"Execution time: {time.time()-start_time} seconds")


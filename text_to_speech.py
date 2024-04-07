from tiktokvoice import tts
from pydub import AudioSegment
from goose3 import Goose
import os, audioread

VOICE = "en_us_006"

def generate_wav(link):
    g = Goose()
    article = g.extract(link)
    text = article.cleaned_text

    #tts(input text, voice, output file, (optional) play sound)
    tts(text, VOICE, "output.mp3")

    sound = AudioSegment.from_mp3("output.mp3")
    sound.export("output.wav", format="wav")
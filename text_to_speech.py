from tiktokvoice import tts
from pydub import AudioSegment
from goose3 import Goose
import os, audioread

def generate_wav(link, voice, output_file):
    g = Goose()
    article = g.extract(link)
    text = article.cleaned_text

    #tts(input text, voice, output file, (optional) play sound)
    tts(text, voice, "output.mp3")

    sound = AudioSegment.from_mp3("output.mp3")
    sound.export(output_file, format="wav")
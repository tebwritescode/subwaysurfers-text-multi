from tiktokvoice import tts
from pydub import AudioSegment
from goose3 import Goose
import os, audioread
import validators

def generate_wav(article, voice, output_file):
    # Check if the input is a URL
    if validators.url(article):
        # If it's a URL, extract text using Goose
        g = Goose()
        extracted_article = g.extract(article)
        text = extracted_article.cleaned_text
    else:
        # If it's not a URL, assume it's direct text
        text = article
    
    # Generate TTS and convert to WAV
    tts(text, voice, "output.mp3")
    sound = AudioSegment.from_mp3("output.mp3")

    sound.export(output_file, format="wav")

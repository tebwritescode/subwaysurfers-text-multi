from tiktokvoice import tts
from pydub import AudioSegment
from goose3 import Goose
from cleantext import cleantext
import os, audioread
import validators

def generate_wav(article, voice, output_file):
    """
    Generate a WAV audio file from text or article URL using text-to-speech.
    
    This function takes either a direct text input or a URL to an article,
    converts the text to speech using TikTok's voice synthesis, and saves
    the result as a WAV file.
    
    Args:
        article (str): Either a URL to an article or direct text content
        voice (str): The voice ID to use for text-to-speech synthesis
        output_file (str): Path where the output WAV file will be saved
    
    Returns:
        None
    
    Note:
        - If article is a valid URL, the function will extract the article text using Goose
        - The function first creates an MP3 file and then converts it to WAV format
    """
    g = Goose()
    # Check if the input is a URL
    if validators.url(article):
        # If it's a URL, extract text using Goose
        extracted_article = g.extract(article)
        text = extracted_article.cleaned_text
    else:
        # If it's not a URL, assume it's direct text
        text = cleantext(article)
    
    # Generate TTS and save as MP3
    tts(text, voice, "output.mp3")
    
    # Convert MP3 to WAV format
    sound = AudioSegment.from_mp3("output.mp3")
    sound.export(output_file, format="wav")

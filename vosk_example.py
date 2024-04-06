import os
import sys
import wave
import json

from vosk import Model, KaldiRecognizer, SetLogLevel
# !pip install vosk
import Word

SetLogLevel(0)

# path to vosk model downloaded from
# https://alphacephei.com/vosk/models
model_path = "/Users/danielbonkowsky/Documents/vosk-model-en-us-0.22"

if not os.path.exists(model_path):
    print(f"Please download the model from https://alphacephei.com/vosk/models and unpack as {model_path}")
    sys.exit()

print(f"Reading your vosk model '{model_path}'...")
model = Model(model_path)
print(f"'{model_path}' model was successfully read")

# name of the audio file to recognize
audio_filename = "output.wav"
# name of the text file to write recognized text
text_filename = "output.txt"

if not os.path.exists(audio_filename):
    print(f"File '{audio_filename}' doesn't exist")
    sys.exit()

print(f"Reading your file '{audio_filename}'...")
wf = wave.open(audio_filename, "rb")
print(f"'{audio_filename}' file was successfully read")

# check if audio is mono wav
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    sys.exit()

rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(True)

results = []

# recognize speech using vosk model
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        part_result = json.loads(rec.Result())
        results.append(part_result)

part_result = json.loads(rec.FinalResult())
results.append(part_result)

# convert list of JSON dictionaries to list of 'Word' objects

list_of_words = []
for sentence in results:
    if len(sentence) == 1:
        # sometimes there are bugs in recognition 
        # and it returns an empty dictionary
        # {'text': ''}
        continue
    for obj in sentence['result']:
        w = Word.Word(obj)  # create custom Word object
        list_of_words.append(w)  # and add it to list

for word in list_of_words:
    print(word.to_string())
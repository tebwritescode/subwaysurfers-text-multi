import os, sys, wave, json, time
from vosk import Model, KaldiRecognizer, SetLogLevel

""" 
path to vosk model downloaded from 
https://alphacephei.com/vosk/models
Currently using the 1.8Gb version 
"""

def get_words_and_timestamps(model_path, audio):
    # If model path doesn't work
    if (not os.path.exists(model_path)):
        print(f"Please download the model from https://alphacephei.com/vosk/models and unpack as {model_path}")
        sys.exit()

    # Reading the vosk model
    model = Model(model_path)

    # name of the audio file to recognize
    audio_filename = audio

    # If audio file doesn't exist
    if (not os.path.exists(audio_filename)):
        print(f"File '{audio_filename}' doesn't exist")
        sys.exit()

    # Reading the audio file
    wf = wave.open(audio_filename, "rb")

    # check if audio is mono wav
    if (wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE"):
        print("Audio file must be WAV format mono PCM.")
        sys.exit()

    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    results = []

    # recognize speech using vosk model
    while (True):
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            part_result = json.loads(rec.Result())
            results.append(part_result)

    part_result = json.loads(rec.FinalResult())
    results.append(part_result)

    words = []
    end_times = []

    for sentence in results:
        if (len(sentence) == 1):
            # sometimes there are bugs in recognition 
            # and it returns an empty dictionary
            # {'text': ''}
            continue
        for obj in sentence["result"]:
            words.append(obj["word"])
            end_times.append(obj["end"])
    
    return words, end_times

if __name__ == "__main__":
    INPUT_FILE = "output.wav"

    start_time = time.time()

    # Turn LOG messages on / off, 0 is on and -1 is off
    SetLogLevel(-1)

    model_path = "/Users/danielbonkowsky/Documents/vosk-model-en-us-0.22"
    w, e = get_words_and_timestamps(model_path=model_path, audio=INPUT_FILE)
    print(w)
    print(e)

    print(f"Execution time: {time.time()-start_time} seconds")

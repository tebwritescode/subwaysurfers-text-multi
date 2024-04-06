from helpers import create_video

# Array of strings to overlay at different timestamps
texts = ['Text 1', 'Text 2', 'Text 3']
textlengths = [2, 5, 8]  # lengths

create_video(texts, textlengths, 15)
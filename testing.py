from videomaker import create_video

# Array of strings to overlay at different timestamps
texts = ['Text 1', 'Text 2', 'Text 3']
timestamps = [5, 8, 10]  # timestamps

create_video(texts, timestamps, 10)
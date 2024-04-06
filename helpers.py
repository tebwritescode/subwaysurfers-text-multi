from moviepy.editor import *
import random

'''

Components:
- video, getting random time stamps
- also need to loop the video

My plan: have the 2 hr vid downloaded and in /static

Input will need limitations - i.e. character limit?

'''

def create_video(texts, textlengths, video_length):
    # generates a video that starts at a random timestamp and length = video_length
    video_path = 'static\\subwaysurfvid.mp4'
    starttimestamp = generate_starttimestamp(video_length)
    video = VideoFileClip(video_path).subclip(starttimestamp, starttimestamp + video_length)

    # finds the correct timestamp for all the texts
    timestamps = []
    timestamps.append(0)
    for i in range(len(textlengths)):
        timestamps.append(timestamps[i] + textlengths[i])

    # makes a list of all the text clips
    text_clips = []
    for i in range(len(texts)):
        text_clip = TextClip(texts[i], fontsize=70, color='black')
        text_clip = text_clip.set_pos('center').set_start(textlengths[i]).set_end(textlengths[i + 1])
        text_clips.append(text_clip)


    # composite the text clips onto the video clip
    final_clip = CompositeVideoClip([video] + text_clips)

    # write the edited video to a temporary file
    edited_video_path = 'static\\edited_vid.mp4'
    final_clip.write_videofile(edited_video_path, codec='libx264')


def generate_starttimestamp(video_length):
    return random.randint(94, 8005 - video_length)


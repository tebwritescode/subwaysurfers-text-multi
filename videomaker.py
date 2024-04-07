import cv2
import random
import time

'''
two lists, one of words and other of ending timestamps
'''

#video_length should be the length of the template video file, should be in seconds
def create_video(words, timestamps, video_length):
    # loading video file
    input_video_path = 'static/subway_surf.mp4'
    output_video_path = 'static/outputvid.mp4'
    starttimestamp = generate_starttimestamp(video_length)
    video = cv2.VideoCapture(input_video_path)
    video.set(cv2.CAP_PROP_POS_MSEC, starttimestamp)

    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter('output_video.mp4', fourcc, fps, (width, height))

    #Define the text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_position = (360, 360)
    font_scale = 1
    font_color = (255, 255, 255)
    thickness = 4

    # Loop through all the words/timestamps
    framestamps = []
    for time in timestamps:
        framestamps.append(int(time * fps))
    
    word_num = 0
    for i in range(video_length * fps):
        if (i == framestamps[word_num] and word_num != len(words)-1):
            word_num += 1

        ret, frame = video.read()
        if (not ret):
            break

        word = words[word_num]
        cv2.putText(frame, word, (300, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        output_video.write(frame)

    # Release the video capture and writer objects
    video.release()
    output_video.release()
    cv2.destroyAllWindows()


def generate_starttimestamp(video_length):
    return 1000000



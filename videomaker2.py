import cv2
import random
import time

'''
two lists, one of words and other of ending timestamps
'''

#video_length should be the length of the template video file, should be in seconds
def create_video(words, timestamps, video_length):
    # loading video file
    input_video_path = 'surf.mp4'
    # output_video_path = 'static\\outputvid.mp4'
    starttimestamp = generate_starttimestamp(video_length)
    video = cv2.VideoCapture(input_video_path)
    video.set(cv2.CAP_PROP_POS_MSEC, starttimestamp)
    # video.set(cv2.CAP_PROP_POS_MSEC, 500)

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
    start_time = time.time()
    for i, (word, end_time) in enumerate(zip(words, timestamps)):
        while time.time() - start_time < end_time/10:
            ret, frame = video.read()
            if not ret:
                break

            # Display the current word on the frame
            cv2.putText(frame, word, text_position, font, font_scale, font_color, thickness)

            # Write the frame to the output video
            output_video.write(frame)

    video.release()
    output_video.release()
    cv2.destroyAllWindows()

def generate_starttimestamp(video_length):
    return random.randint(500, 5000 - video_length) * 10

    # Release the video capture and writer objects
import cv2
import random
import time

'''
two lists, one of words and other of ending timestamps
'''

#video_length should be the length of the template video file, should be in seconds
def create_video(words, timestamps, video_length):
    # loading video file
    input_video_path = "surf.mp4"
    video = cv2.VideoCapture(input_video_path)

    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter('output_video.mp4', fourcc, fps, (width, height))

    # Define the text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_position = (50, 50)
    font_scale = 2
    font_color = (0, 0, 0)
    thickness = 4

    # Initialize variables for timing
    start_time = time.time()
    current_timestamp_idx = 0

    # Loop through all the words/timestamps
    while current_timestamp_idx < len(timestamps):
        ret, frame = video.read()
        if not ret:
            break

        # current_time = time.time() - start_time  # Adjust to measure time relative to start_time
        # # Check if it's time to change the word based on the timestamp
        # if current_time >= timestamps[current_timestamp_idx]:
        #     # Display the current word on the frame
        #     #cv2.putText(frame, words[current_timestamp_idx], text_position, font, font_scale, font_color, thickness)
        #     cv2.putText(frame, "hi"+str(current_timestamp_idx), text_position, font, font_scale, font_color, thickness)
        #     current_timestamp_idx += 1  # Move to the next timestamp

        cv2.putText(frame, "hi", text_position, font, font_scale, font_color, thickness)


        # Write the frame to the output video
        output_video.write(frame)

    # Release the video capture and writer objects
    video.release()
    output_video.release()
    cv2.destroyAllWindows()

words = ["word1", "word2", "word3"]  # List of words
timestamps = [10, 20, 30]  # List of timestamps (in seconds) indicating when to change the word
video_length = 100  # Length of the video in seconds
create_video(words, timestamps, video_length)
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
    video = cv2.VideoCapture(input_video_path)
    video.set(cv2.CAP_PROP_POS_MSEC, 1000000)

    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter('output_video.mp4', fourcc, fps, (width, height))

    #Define the text properties
    font = cv2.FONT_HERSHEY_PLAIN
    # text_position = (296, 640)
    font_scale = 3
    font_color = (255, 255, 255)
    thickness = 5
    outline_thickness = 10

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
        
        # Get the size of the text
        text_size = cv2.getTextSize(word, font, font_scale, thickness)[0]

        # Calculate the position to center the text
        text_position = ((width - text_size[0]) // 2, (height + text_size[1]) // 2)
        cv2.putText(frame, word, text_position, font, font_scale, (0, 0, 0), outline_thickness)
        cv2.putText(frame, word, text_position, font, font_scale, font_color, thickness)
        output_video.write(frame)

    # Release the video capture and writer objects
    video.release()
    output_video.release()
    cv2.destroyAllWindows()




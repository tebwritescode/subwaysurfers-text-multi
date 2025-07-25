import cv2
import random
import time

'''
two lists, one of words and other of ending timestamps
'''

#video_length should be the length of the template video file, should be in seconds

def create_video(words, timestamps, video_length, source_video, output_video):
    # loading video file
    video = cv2.VideoCapture(source_video)

    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # start at a random location 0 to 30 minutes remaining
    video.set(cv2.CAP_PROP_POS_MSEC, random.randint(10 * fps, 30 * 60 * fps))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Define the text properties
    font = cv2.FONT_HERSHEY_PLAIN
    font_scale = 3
    font_color = (255, 255, 255)
    thickness = 5
    outline_thickness = 10

    # Convert timestamps to frame indices
    framestamps = [int(time * fps) for time in timestamps]

    # Defensive: Ensure framestamps and words are the same length
    if len(framestamps) != len(words):
        min_len = min(len(framestamps), len(words))
        framestamps = framestamps[:min_len]
        words = words[:min_len]

    # Add a final frame index to mark the end of the last word
    framestamps.append(video_length * fps)

    word_num = 0
    for i in range(video_length * fps):
        # Advance word_num if we've reached the next framestamp
        if word_num + 1 < len(framestamps) and i >= framestamps[word_num + 1]:
            word_num += 1
        # Defensive: If word_num is out of bounds, break
        if word_num >= len(words):
            break

        ret, frame = video.read()
        if not ret:
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




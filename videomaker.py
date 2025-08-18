import cv2
import random
import time
import logging

# Set up logging for videomaker
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

'''
two lists, one of words and other of ending timestamps
'''

#video_length should be the length of the template video file, should be in seconds

def create_video(words, timestamps, video_length, source_video, output_video, progress_queue=None, progress_start=25, progress_end=85):
    logger.info(f"Creating video with {len(words)} words, {len(timestamps)} timestamps, {video_length}s duration")
    logger.info(f"Source video: {source_video}, Output: {output_video}")
    
    def update_video_progress(current_frame, total_frames):
        """Update progress during video creation."""
        if progress_queue:
            try:
                # Calculate progress within the video creation range (progress_start to progress_end)
                frame_progress = (current_frame / total_frames)
                overall_progress = progress_start + (frame_progress * (progress_end - progress_start))
                
                # Update every 5% or every 60 frames (whichever is more frequent) to avoid spam
                if current_frame % max(1, total_frames // 20) == 0 or current_frame % 60 == 0:
                    progress_queue.put({
                        'progress': min(overall_progress, progress_end),
                        'step': 'video',
                        'message': f"Rendering frame {current_frame}/{total_frames} ({frame_progress*100:.1f}%)"
                    })
            except:
                pass  # Don't fail if progress update fails
    
    # loading video file
    video = cv2.VideoCapture(source_video)

    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    logger.info(f"Video properties: {width}x{height} @ {fps} FPS")

    # start at a random location 10 seconds to 30 minutes into the video
    start_time_ms = random.randint(10 * 1000, 30 * 60 * 1000)  # 10 seconds to 30 minutes in milliseconds
    video.set(cv2.CAP_PROP_POS_MSEC, start_time_ms)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_video = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    # Define the text properties
    font = cv2.FONT_HERSHEY_PLAIN
    font_scale = 3
    font_color = (255, 255, 255)
    thickness = 5
    outline_thickness = 10

    # Convert timestamps to frame indices (using round for better accuracy)
    framestamps = [round(time * fps) for time in timestamps]
    
    logger.info(f"First 5 timestamps: {timestamps[:5]}")
    logger.info(f"First 5 framestamps: {framestamps[:5]}")

    # Defensive: Ensure framestamps and words are the same length
    if len(framestamps) != len(words):
        logger.warning(f"Mismatch: {len(words)} words vs {len(framestamps)} timestamps")
        min_len = min(len(framestamps), len(words))
        framestamps = framestamps[:min_len]
        words = words[:min_len]
        logger.info(f"Truncated to {min_len} words/timestamps")

    # Add a final frame index to mark the end of the last word
    total_frames = int(video_length * fps)
    framestamps.append(total_frames)
    logger.info(f"Total frames to generate: {total_frames}")

    word_num = 0
    current_word = ""
    last_word_change_frame = -1
    
    for i in range(total_frames):
        # Update progress
        update_video_progress(i, total_frames)
        
        # Advance word_num if we've reached the next framestamp
        if word_num + 1 < len(framestamps) and i >= framestamps[word_num + 1]:
            word_num += 1
            if word_num < len(words):
                logger.info(f"Frame {i}: Switching to word {word_num}: '{words[word_num]}'")
                last_word_change_frame = i
        
        # Defensive: If word_num is out of bounds, break
        if word_num >= len(words):
            logger.warning(f"Frame {i}: word_num {word_num} >= len(words) {len(words)}")
            break

        ret, frame = video.read()
        if not ret:
            logger.error(f"Failed to read frame {i} from video")
            break

        word = words[word_num]
        
        # Log word changes for debugging (only for first few to reduce log spam)
        if word != current_word and i < 100:
            current_word = word
            if last_word_change_frame != i:
                logger.warning(f"Frame {i}: Word changed to '{word}' but framestamp not triggered")

        # Get the size of the text
        text_size = cv2.getTextSize(word, font, font_scale, thickness)[0]

        # Calculate the position to center the text
        text_position = ((width - text_size[0]) // 2, (height + text_size[1]) // 2)
        cv2.putText(frame, word, text_position, font, font_scale, (0, 0, 0), outline_thickness)
        cv2.putText(frame, word, text_position, font, font_scale, font_color, thickness)
        output_video.write(frame)
    
    # Final progress update for video creation
    if progress_queue:
        try:
            progress_queue.put({
                'progress': progress_end,
                'step': 'video',
                'message': 'Video rendering completed'
            })
        except:
            pass

    # Release the video capture and writer objects
    video.release()
    output_video.release()
    cv2.destroyAllWindows()




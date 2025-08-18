import cv2
import random
import os
import logging
from whisper_timestamper import get_words_and_timestamps_whisper

logger = logging.getLogger(__name__)

def create_video_without_captions(video_length, source_video, output_video):
    """
    STEP 1: Generate video WITHOUT captions but WITH voiceover
    This creates the base video that we'll add captions to later
    """
    logger.info("Step 1: Creating video without captions...")
    
    # Loading video file
    video = cv2.VideoCapture(source_video)
    
    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Random start position (0-10 seconds like original)
    video.set(cv2.CAP_PROP_POS_MSEC, random.randint(0, 10) * fps)
    
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_writer = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    logger.info(f"Generating {video_length}s video at {fps}fps ({width}x{height})")
    
    total_frames = int(video_length * fps)
    for frame_num in range(total_frames):
        ret, frame = video.read()
        if not ret:
            break
        
        # Write frame without any captions
        output_writer.write(frame)
        
        if frame_num % (fps * 10) == 0:  # Log every 10 seconds
            logger.info(f"Generated {frame_num // fps}s of video...")
    
    # Release resources
    video.release()
    output_writer.release()
    cv2.destroyAllWindows()
    
    logger.info(f"Step 1 complete: Video without captions saved to {output_video}")
    return output_video

def generate_subtitles_with_whisper(audio_file_path, whisper_server_url=None):
    """
    STEP 2: Generate word-level subtitles using Whisper ASR
    """
    logger.info("Step 2: Generating subtitles with Whisper ASR...")
    
    try:
        words, timestamps = get_words_and_timestamps_whisper(audio_file_path, whisper_server_url)
        
        logger.info(f"Whisper generated {len(words)} words with timestamps")
        logger.info(f"Sample: {list(zip(words[:5], timestamps[:5]))}")
        
        return words, timestamps
        
    except Exception as e:
        logger.error(f"Whisper subtitle generation failed: {e}")
        raise

def add_captions_to_video(base_video_path, words, timestamps, output_video_path):
    """
    STEP 3: Add captions to video using Whisper timestamps
    """
    logger.info("Step 3: Adding captions to video using Whisper timestamps...")
    
    # Load the base video (without captions)
    video = cv2.VideoCapture(base_video_path)
    
    # Get video properties
    fps = int(video.get(cv2.CAP_PROP_FPS))
    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Define text properties
    font = cv2.FONT_HERSHEY_PLAIN
    font_scale = 3
    font_color = (255, 255, 255)
    thickness = 5
    outline_thickness = 10
    
    # Create word schedule with Whisper timestamps
    word_schedule = []
    for i, (word, start_time) in enumerate(zip(words, timestamps)):
        # Calculate end time for this word
        if i < len(timestamps) - 1:
            end_time = timestamps[i + 1]
        else:
            end_time = start_time + 1.0  # Show last word for 1 second
        
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)
        
        word_schedule.append({
            'word': word,
            'start_frame': start_frame,
            'end_frame': end_frame,
            'start_time': start_time,
            'end_time': end_time
        })
        
        if i < 10:  # Log first 10 words
            logger.info(f"Word {i}: '{word}' from {start_time:.2f}s to {end_time:.2f}s (frames {start_frame}-{end_frame})")
    
    logger.info(f"Processing {total_frames} frames with {len(word_schedule)} words...")
    
    # Process each frame and add appropriate caption
    for frame_num in range(total_frames):
        ret, frame = video.read()
        if not ret:
            break
        
        # Find which word should be displayed at this frame
        current_word = ""
        for word_info in word_schedule:
            if word_info['start_frame'] <= frame_num < word_info['end_frame']:
                current_word = word_info['word']
                break
        
        # Add caption if there's a word to display
        if current_word:
            # Get the size of the text
            text_size = cv2.getTextSize(current_word, font, font_scale, thickness)[0]
            
            # Calculate centered position
            text_position = ((width - text_size[0]) // 2, (height + text_size[1]) // 2)
            
            # Draw text with outline
            cv2.putText(frame, current_word, text_position, font, font_scale, (0, 0, 0), outline_thickness)
            cv2.putText(frame, current_word, text_position, font, font_scale, font_color, thickness)
        
        output_writer.write(frame)
        
        if frame_num % (fps * 10) == 0:  # Log every 10 seconds
            logger.info(f"Added captions to {frame_num // fps}s of video...")
    
    # Release resources
    video.release()
    output_writer.release()
    cv2.destroyAllWindows()
    
    logger.info(f"Step 3 complete: Final video with captions saved to {output_video_path}")
    return output_video_path

def create_video_new_pipeline(text, video_length, source_video, audio_file, final_output, whisper_server_url=None):
    """
    MAIN FUNCTION: New 3-step pipeline
    1. Generate video without captions but with voiceover
    2. Generate subtitles using Whisper ASR 
    3. Add captions to video using Whisper timestamps
    """
    logger.info("Starting new 3-step video generation pipeline...")
    
    # Step 1: Create video without captions
    base_video_path = "base_video_no_captions.mp4"
    create_video_without_captions(video_length, source_video, base_video_path)
    
    # Step 2: Generate subtitles with Whisper
    words, timestamps = generate_subtitles_with_whisper(audio_file, whisper_server_url)
    
    # Step 3: Add captions using Whisper timestamps
    add_captions_to_video(base_video_path, words, timestamps, final_output)
    
    # Clean up intermediate file
    if os.path.exists(base_video_path):
        os.remove(base_video_path)
        logger.info("Cleaned up intermediate base video file")
    
    logger.info("New pipeline complete!")
    return final_output
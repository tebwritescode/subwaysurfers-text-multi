from new_pipeline import create_video_new_pipeline
from whisper_timestamper import get_words_and_timestamps_whisper
from text_to_speech import generate_wav
from text_splitter import split_text_into_sections, get_section_count_and_info
from word_aligner import align_words_with_timestamps
from cleantext import cleantext
import subprocess
import ffmpeg
import os
import shutil
# import audioread - removed for Python 3.13 compatibility
from pydub import AudioSegment
import time
import random
import logging
import sys
import traceback
import validators

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

"""
CONSTANTS AND CONFIGURATION
"""
MODEL_PATH = os.getenv('MODEL_PATH', "static/vosk-model-en-us-0.22")
SOURCE_VIDEO_DIR = os.getenv('SOURCE_VIDEO_DIR', "static")
WAV_FILE = "output.wav"
FAST_WAV_FILE = "output_fast.wav"
MP3_FILE = "output.mp3"
CAPTION_VIDEO = "output_caption.mp4"
PRE_OUTPUT_VIDEO = "output_wrong_encoding.mp4"
OUTPUT_VIDEO = "final.mp4"

"""
FUNCTIONS
"""

def get_source_video(source_path=SOURCE_VIDEO_DIR):
    """
    Gets a video file based on the source path.
    If source_path is a file, returns that file.
    If source_path is a directory, selects a random video from it.
    Filters out small files (likely corrupted or output files) when selecting from directory.

    Args:
        source_path (str): Path to a video file or directory containing video files.
    
    Returns:
        str or dict: Path to the video file or an error message.
    """
    try:
        # Check if source_path is a file
        if os.path.isfile(source_path):
            if source_path.lower().endswith('.mp4'):
                # Verify file size
                file_size = os.path.getsize(source_path)
                if file_size > 50 * 1024 * 1024:  # 50MB minimum
                    logger.info(f"Using specified video file: {source_path}")
                    return source_path
                else:
                    return {"error": f"Video file too small ({file_size} bytes), expected > 50MB: {source_path}"}
            else:
                return {"error": f"Invalid video file format (expected .mp4): {source_path}"}
        
        # Check if source_path is a directory
        elif os.path.isdir(source_path):
            video_files = []
            for f in os.listdir(source_path):
                if f.lower().endswith('.mp4'):
                    full_path = os.path.join(source_path, f)
                    try:
                        # Only include files larger than 50MB (source videos should be large)
                        file_size = os.path.getsize(full_path)
                        if file_size > 50 * 1024 * 1024:  # 50MB minimum
                            video_files.append(full_path)
                        else:
                            logger.warning(f"Skipping small video file: {f} ({file_size} bytes)")
                    except OSError:
                        logger.warning(f"Could not get size for: {f}")
                        continue
            
            if not video_files:
                return {"error": f"No valid large video files found in directory \"{source_path}\""}

            selected_video = random.choice(video_files)
            logger.info(f"Randomly selected video from directory: {selected_video}")
            return selected_video
        
        else:
            return {"error": f"Source path not found: {source_path}"}
        
    except Exception as e:
        logger.error(f"Error in get_source_video: {str(e)}")
        logger.debug(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

def verify_vosk_model():
    """
    Checks if the Vosk model directory exists and contains required files.

    Returns:
        dict: {"error": "message"} if model is missing or corrupted, otherwise {}
    """
    if not os.path.exists(MODEL_PATH):
        return {"error": f"Missing Vosk model directory: \"{MODEL_PATH}\""}

    required_files = ["README", "am", "conf", "graph", "ivector", "rescore", "rnnlm"]
    missing_files = [f for f in required_files if not os.path.exists(os.path.join(MODEL_PATH, f))]
    
    if missing_files:
        return {"error": f"Incomplete Vosk model: Missing \"{MODEL_PATH}/{', '.join(missing_files)}\""}
    
    return {}

def speed_up_audio(input_file, output_file, speed_factor):
    """
    Speeds up an audio file using FFmpeg's atempo filter.

    Parameters:
        input_file (str): Path to the input audio file.
        output_file (str): Path to the output audio file.
        speed_factor (float): Speed factor (e.g., 1.0 for normal speed, 1.5 for 1.5x speed).

    Returns:
        dict: Success message or error description.
    """
    try:
        if speed_factor < 0.5:
            return {"error": "Speed factor too low. Minimum allowed is 0.5x."}

        if not os.path.exists(input_file):
            return {"error": f"Input audio file missing: {input_file}"}

        command = ["ffmpeg", "-i", input_file, "-filter:a", f"atempo={speed_factor}", "-vn", output_file]
        subprocess.run(command, check=True)

        return {"success": f"Audio sped up by {speed_factor}x and saved as {output_file}"}

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error in speed_up_audio: {e}")
        logger.debug(traceback.format_exc())
        return {"error": f"FFmpeg error: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in speed_up_audio: {e}")
        logger.debug(traceback.format_exc())
        return {"error": f"Unexpected error: {str(e)}"}

def validate_text_input(text):
    """Throws an exception if the input contains fewer than 10 words."""
    word_count = len(text.split())  # Count words by splitting on spaces
    if word_count < 10:
        raise ValueError(f"Input contains only {word_count} words. A minimum of 10 is required.")
    return f"Valid input with {word_count} words."

def script(input_text, customspeed, customvoice, final_path="final.mp4", progress_queue=None):
    """
    Processes text input and generates a video with captions.
    Handles long texts by splitting them into sections and merging the final videos.

    Args:
        input_text (str): Text to convert to speech.
        customspeed (float): Speech playback speed adjustment.
        customvoice (str): Voice selection for text-to-speech.
        final_path (str): Path to save the final video.
        progress_queue (queue.Queue, optional): Queue for progress updates.

    Returns:
        dict: Success or error message.
    """
    
    def update_progress(progress, step, message):
        """Send progress update if queue is available."""
        if progress_queue:
            try:
                progress_queue.put({
                    'progress': progress,
                    'step': step,
                    'message': message
                })
            except:
                pass  # Don't fail if progress update fails

    def process_single_section(text_section, section_num, total_sections, progress_start, progress_end, source_video):
        """Process a single text section and return the path to the generated video."""
        section_suffix = f"_section_{section_num}" if total_sections > 1 else ""
        section_wav = f"output{section_suffix}.wav"
        section_fast_wav = f"output_fast{section_suffix}.wav"
        section_caption_video = f"output_caption{section_suffix}.mp4"
        section_final_video = f"section_{section_num}.mp4"
        
        try:
            # Generate TTS for this section
            progress_step = progress_start + (progress_end - progress_start) * 0.1
            update_progress(int(progress_step), "audio", f"Generating TTS for section {section_num}/{total_sections}...")
            
            tts_response = generate_wav(text_section, customvoice, section_wav)
            if tts_response and "error" in tts_response:
                return {"error": f"TTS generation failed for section {section_num}: {tts_response['error']}"}

            # Adjust playback speed
            progress_step = progress_start + (progress_end - progress_start) * 0.2
            update_progress(int(progress_step), "audio", f"Adjusting playback speed for section {section_num}...")
            
            speed_response = speed_up_audio(section_wav, section_fast_wav, customspeed)
            if isinstance(speed_response, dict) and "error" in speed_response:
                return {"error": f"Speed adjustment failed for section {section_num}: {speed_response['error']}"}

            # Extract words and timestamps
            progress_step = progress_start + (progress_end - progress_start) * 0.3
            update_progress(int(progress_step), "processing", f"Analyzing speech for section {section_num}...")
            
            try:
                stt_words, stt_timestamps = get_words_and_timestamps_whisper(section_fast_wav)
            except Exception as e:
                return {"error": f"Speech recognition failed for section {section_num}: {str(e)}"}

            # TEMPORARILY DISABLED - Using STT words directly to test timing
            logger.info(f"TESTING: Using STT words directly without alignment for section {section_num}")
            # aligned_words, aligned_timestamps = align_words_with_timestamps(
            #     text_section, stt_words, stt_timestamps
            # )
            aligned_words, aligned_timestamps = stt_words, stt_timestamps
            
            # Get audio duration using pydub instead of audioread (Python 3.13 compatibility)
            try:
                audio = AudioSegment.from_wav(section_fast_wav)
                sound_duration = int(len(audio) / 1000)  # Convert milliseconds to seconds
            except Exception as e:
                return {"error": f"Failed to determine audio duration for section {section_num}: {str(e)}"}

            # Create captioned video using original text with STT timing
            progress_start_video = progress_start + (progress_end - progress_start) * 0.4
            progress_end_video = progress_start + (progress_end - progress_start) * 0.9
            update_progress(int(progress_start_video), "video", f"Creating video for section {section_num}/{total_sections}...")
            
            try:
                # Use the new WhisperASR-based pipeline for perfect timing
                create_video_new_pipeline(text_section, sound_duration, source_video, section_fast_wav, section_caption_video)
            except Exception as e:
                return {"error": f"Video creation failed for section {section_num}: {str(e)}"}

            # Merge video and audio for this section
            progress_step = progress_start + (progress_end - progress_start) * 0.95
            update_progress(int(progress_step), "merge", f"Merging section {section_num} video and audio...")
            
            concat_cmd = f"bash concat.sh {section_caption_video} {section_fast_wav} output_temp_{section_num}.mp4 \"{section_final_video}\""
            logger.info(f"Executing: {concat_cmd}")
            concat_result = os.system(concat_cmd)
            if concat_result != 0:
                return {"error": f"Video merging failed for section {section_num} with exit code {concat_result}"}
            
            if not os.path.exists(section_final_video):
                return {"error": f"Section {section_num} video was not created"}
                
            return {"success": section_final_video}
            
        except Exception as e:
            logger.error(f"Error processing section {section_num}: {str(e)}")
            return {"error": f"Section {section_num} processing failed: {str(e)}"}

    try:
        update_progress(2, "validation", "Validating and cleaning input text...")
        
        # Clean the text once at the beginning
        if validators.url(input_text):
            logger.info("URL detected, text will be extracted and cleaned by TTS module")
            # For URLs, let text_to_speech.py handle extraction and cleaning
            cleaned_input_text = input_text
        else:
            logger.info("Text input detected, cleaning text...")
            cleaned_input_text = cleantext(input_text)
            
            # Validate cleaned text has at least 10 words
            word_count = len(cleaned_input_text.split())
            if word_count < 10:
                raise ValueError(f"Cleaned text must contain at least 10 words (found {word_count})")

        update_progress(4, "validation", "Using ElevenLabs TTS...")

        # Skip Vosk model check since we're using ElevenLabs TTS
        # model_check = verify_vosk_model()
        # if "error" in model_check:
        #     return model_check

        update_progress(6, "setup", "Analyzing text length and planning sections...")

        # Split text into sections if needed (already cleaned)
        if validators.url(cleaned_input_text):
            # For URLs, splitting will be handled after extraction
            text_sections = [cleaned_input_text]
        else:
            # For text input, split the already cleaned text
            text_sections = split_text_into_sections(cleaned_input_text)
        section_count = len(text_sections)
        
        logger.info(f"Text split into {section_count} sections")
        
        if section_count > 1:
            update_progress(8, "setup", f"Processing {section_count} text sections...")
        else:
            update_progress(8, "setup", "Processing single text section...")

        # Get background video
        update_progress(10, "setup", "Selecting background video...")
        source_video = get_source_video()
        if isinstance(source_video, dict) and "error" in source_video:
            return source_video

        logger.info(f"Source Video Selected: {source_video}")

        # Clean up previous files
        update_progress(12, "setup", "Cleaning up previous files...")
        os.system(f"bash clean.sh {OUTPUT_VIDEO}")

        # Process each section
        section_videos = []
        progress_per_section = 70 / section_count  # 70% of progress for processing sections (15% to 85%)
        
        for i, section_text in enumerate(text_sections, 1):
            section_progress_start = 15 + (i - 1) * progress_per_section
            section_progress_end = 15 + i * progress_per_section
            
            result = process_single_section(section_text, i, section_count, section_progress_start, section_progress_end, source_video)
            if "error" in result:
                return result
            
            section_videos.append(result["success"])

        update_progress(85, "merge", "Merging all sections into final video...")

        # Merge all section videos if multiple sections
        if len(section_videos) > 1:
            # Create a list file for ffmpeg
            list_file = "section_list.txt"
            with open(list_file, 'w') as f:
                for video in section_videos:
                    f.write(f"file '{video}'\n")
            
            # Use ffmpeg to concatenate videos
            merge_cmd = f"ffmpeg -f concat -safe 0 -i {list_file} -c copy \"{final_path}\" -y"
            logger.info(f"Merging sections: {merge_cmd}")
            merge_result = os.system(merge_cmd)
            
            if merge_result != 0:
                return {"error": f"Final video merging failed with exit code {merge_result}"}
                
            # Clean up section files
            for video in section_videos:
                if os.path.exists(video):
                    os.remove(video)
            if os.path.exists(list_file):
                os.remove(list_file)
        else:
            # Single section - just move to final path
            if section_videos:
                shutil.move(section_videos[0], final_path)

        update_progress(95, "finalizing", "Verifying final output...")
        
        # Verify the final output exists
        if not os.path.exists(final_path):
            return {"error": f"Final video was not created at {final_path}"}

        update_progress(100, "completed", f"Multi-section video generation completed! ({section_count} sections processed)")
        return {"success": f"Video generation completed with {section_count} sections."}

    except Exception as e:
        logger.error(f"Unexpected error in script: {str(e)}")
        logger.debug(traceback.format_exc())
        return {"error": f"Script execution failed: {str(e)}"}

# Test the function when running this script directly
if __name__ == "__main__":
    sample_input = "This is a test sentence."
    print(script(sample_input, 1.0, "en_us_rocket"))

"""
Word alignment module to map original text words to STT timestamps.
This ensures captions show the exact original text while using STT for timing.
"""

import re
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def tokenize_text(text):
    """
    Split text into words, preserving punctuation as separate tokens where needed.
    
    Args:
        text (str): The input text to tokenize
        
    Returns:
        list: List of words/tokens
    """
    # Simple word tokenization that treats punctuation attached to words as part of the word
    # This matches how TTS typically pronounces text
    words = re.findall(r'\b\w+[\w\']*\b|[^\w\s]+', text)
    # Filter out empty strings and standalone punctuation that won't be spoken
    words = [w for w in words if w and not re.match(r'^[^\w]+$', w)]
    return words

def align_words_with_timestamps(original_text, stt_words, stt_timestamps):
    """
    Align original text words with STT timestamps.
    
    This function maps each word from the original text to the most appropriate
    timestamp from the STT results, handling cases where STT may have 
    transcribed words differently.
    
    Args:
        original_text (str): The original input text
        stt_words (list): Words recognized by STT
        stt_timestamps (list): End timestamps for each STT word
        
    Returns:
        tuple: (aligned_words, aligned_timestamps) - original words with matched timestamps
    """
    # Tokenize the original text
    original_words = tokenize_text(original_text)
    
    if not original_words:
        return [], []
    
    if not stt_words or not stt_timestamps:
        logger.warning("No STT results to align with")
        # Create evenly spaced timestamps as fallback
        total_duration = stt_timestamps[-1] if stt_timestamps else 10.0
        spacing = total_duration / len(original_words)
        return original_words, [spacing * (i + 1) for i in range(len(original_words))]
    
    # Use sequence matching to align original words with STT words
    matcher = SequenceMatcher(None, 
                            [w.lower() for w in original_words], 
                            [w.lower() for w in stt_words])
    
    aligned_timestamps = []
    stt_index = 0
    
    # Get matching blocks
    matching_blocks = matcher.get_matching_blocks()
    
    # Create a mapping of original word indices to STT indices
    original_to_stt = {}
    for orig_start, stt_start, length in matching_blocks:
        for i in range(length):
            if orig_start + i < len(original_words) and stt_start + i < len(stt_words):
                original_to_stt[orig_start + i] = stt_start + i
    
    # Assign timestamps to original words
    last_timestamp = 0
    for i, word in enumerate(original_words):
        if i in original_to_stt:
            # Direct match found
            stt_idx = original_to_stt[i]
            timestamp = stt_timestamps[stt_idx]
            last_timestamp = timestamp
        else:
            # No direct match - interpolate based on surrounding matches
            # Find previous and next matched indices
            prev_match_idx = None
            next_match_idx = None
            
            for j in range(i - 1, -1, -1):
                if j in original_to_stt:
                    prev_match_idx = j
                    break
                    
            for j in range(i + 1, len(original_words)):
                if j in original_to_stt:
                    next_match_idx = j
                    break
            
            if prev_match_idx is not None and next_match_idx is not None:
                # Interpolate between previous and next timestamps
                prev_stt_idx = original_to_stt[prev_match_idx]
                next_stt_idx = original_to_stt[next_match_idx]
                prev_time = stt_timestamps[prev_stt_idx]
                next_time = stt_timestamps[next_stt_idx]
                
                # Linear interpolation
                words_between = next_match_idx - prev_match_idx
                word_position = i - prev_match_idx
                timestamp = prev_time + (next_time - prev_time) * (word_position / words_between)
            elif prev_match_idx is not None:
                # Only previous match - extrapolate forward
                prev_stt_idx = original_to_stt[prev_match_idx]
                prev_time = stt_timestamps[prev_stt_idx]
                # Estimate based on average word duration
                avg_word_duration = prev_time / (prev_match_idx + 1) if prev_match_idx > 0 else 0.3
                timestamp = prev_time + avg_word_duration * (i - prev_match_idx)
            elif next_match_idx is not None:
                # Only next match - extrapolate backward
                next_stt_idx = original_to_stt[next_match_idx]
                next_time = stt_timestamps[next_stt_idx]
                # Estimate based on position
                timestamp = next_time * (i + 1) / (next_match_idx + 1)
            else:
                # No matches at all - distribute evenly
                if stt_timestamps:
                    total_duration = stt_timestamps[-1]
                    timestamp = total_duration * (i + 1) / len(original_words)
                else:
                    timestamp = (i + 1) * 0.3  # Default 0.3s per word
            
            # Ensure monotonic timestamps
            timestamp = max(timestamp, last_timestamp + 0.01)
            last_timestamp = timestamp
        
        aligned_timestamps.append(timestamp)
    
    # Log alignment quality
    match_ratio = len(original_to_stt) / len(original_words) if original_words else 0
    logger.info(f"Word alignment: {len(original_words)} original words, "
                f"{len(stt_words)} STT words, {match_ratio:.1%} matched")
    
    if match_ratio < 0.8:
        logger.warning(f"Low word alignment match ratio: {match_ratio:.1%}")
    
    return original_words, aligned_timestamps

def test_alignment():
    """Test the alignment function with sample data."""
    original = "Hello world, this is a test of the word alignment system."
    stt_words = ["hello", "world", "this", "is", "a", "test", "of", "the", "word", "alignment", "system"]
    stt_timestamps = [0.5, 1.0, 1.3, 1.5, 1.7, 2.0, 2.2, 2.4, 2.7, 3.2, 3.8]
    
    aligned_words, aligned_timestamps = align_words_with_timestamps(original, stt_words, stt_timestamps)
    
    print("Original words:", aligned_words)
    print("Aligned timestamps:", aligned_timestamps)
    print("\nAlignment:")
    for word, timestamp in zip(aligned_words, aligned_timestamps):
        print(f"  {timestamp:.2f}s - {word}")

if __name__ == "__main__":
    test_alignment()
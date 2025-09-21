"""
Word aligner module - stub implementation
"""

def align_words_with_timestamps(words, timestamps):
    """
    Align words with timestamps for subtitle generation
    """
    # Simple stub that returns aligned words
    aligned = []
    for i, word in enumerate(words):
        aligned.append({
            'word': word,
            'start': i * 0.5,
            'end': (i + 1) * 0.5
        })
    return aligned
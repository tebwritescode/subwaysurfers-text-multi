import re
from cleantext import cleantext

def split_text_into_sections(text, max_chars=15000, overlap_sentences=2):
    """
    Split long text into manageable sections for TTS processing.
    NOTE: Expects text to already be cleaned by the caller.
    
    Args:
        text (str): The input text to split (should be pre-cleaned)
        max_chars (int): Maximum characters per section (default: 15000)
        overlap_sentences (int): Number of sentences to overlap between sections
        
    Returns:
        list: List of text sections
    """
    # Text should already be cleaned by the caller
    
    # If text is short enough, return as single section
    if len(text) <= max_chars:
        return [text]
    
    # Split into sentences using multiple delimiters
    sentences = re.split(r'[.!?]+\s+', text)
    
    # Filter out very short sentences (likely artifacts)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    sections = []
    current_section = ""
    current_sentences = []
    
    for i, sentence in enumerate(sentences):
        # Check if adding this sentence would exceed the limit
        potential_section = current_section + " " + sentence if current_section else sentence
        
        if len(potential_section) <= max_chars:
            # Safe to add this sentence
            current_section = potential_section
            current_sentences.append(sentence)
        else:
            # Adding this sentence would exceed limit
            if current_section:
                # Save current section
                sections.append(current_section.strip())
                
                # Start new section with overlap
                overlap_start = max(0, len(current_sentences) - overlap_sentences)
                overlap_sentences_list = current_sentences[overlap_start:]
                
                current_section = " ".join(overlap_sentences_list + [sentence])
                current_sentences = overlap_sentences_list + [sentence]
            else:
                # Single sentence is too long, split it by words
                words = sentence.split()
                section_words = []
                
                for word in words:
                    test_section = " ".join(section_words + [word])
                    if len(test_section) <= max_chars:
                        section_words.append(word)
                    else:
                        if section_words:
                            sections.append(" ".join(section_words))
                        section_words = [word]
                
                if section_words:
                    current_section = " ".join(section_words)
                    current_sentences = [current_section]
    
    # Add the last section if it exists
    if current_section.strip():
        sections.append(current_section.strip())
    
    # Ensure all sections have meaningful content
    sections = [s for s in sections if len(s.strip()) > 50]
    
    return sections

def get_section_count_and_info(text):
    """
    Get information about how the text will be split.
    
    Args:
        text (str): Input text
        
    Returns:
        dict: Information about sections including count, estimated duration per section
    """
    sections = split_text_into_sections(text)
    
    return {
        "section_count": len(sections),
        "sections": sections,
        "total_chars": sum(len(s) for s in sections),
        "avg_chars_per_section": sum(len(s) for s in sections) / len(sections) if sections else 0,
        "estimated_minutes_per_section": (sum(len(s) for s in sections) / len(sections)) / 800 if sections else 0  # ~800 chars per minute for TTS
    }

if __name__ == "__main__":
    # Test the splitter
    test_text = """
    This is a very long text that needs to be split into multiple sections. 
    Each section should be manageable for text-to-speech processing while maintaining context.
    The splitter should handle sentence boundaries properly and provide some overlap between sections.
    """ * 50
    
    result = get_section_count_and_info(test_text)
    print(f"Sections: {result['section_count']}")
    print(f"Avg chars per section: {result['avg_chars_per_section']:.0f}")
    print(f"Estimated minutes per section: {result['estimated_minutes_per_section']:.1f}")
import re
def cleantext_disabled(text):
    """TEMPORARILY DISABLED - returns text unchanged for testing"""
    return text

# Temporarily use disabled version for testing
cleantext = cleantext_disabled

def cleantext_original(text):
    """
    Clean text by replacing elements not suitable for TTS with descriptions.
    Ensures that duplicate placeholders are merged into a single instance.
    Args:
        text (str): The input text to clean
    Returns:
        str: The cleaned text with problematic elements replaced
    """
    def ip_to_words(ip):
        """Convert an IP address to spelled-out words"""
        parts = ip.split('.')
        spelled_parts = []
        for part in parts:
            spelled_part = ' '.join(["Zero" if digit == "0" else
                                     "One" if digit == "1" else
                                     "Two" if digit == "2" else
                                     "Three" if digit == "3" else
                                     "Four" if digit == "4" else
                                     "Five" if digit == "5" else
                                     "Six" if digit == "6" else
                                     "Seven" if digit == "7" else
                                     "Eight" if digit == "8" else
                                     "Nine" for digit in part])
            spelled_parts.append(spelled_part)
        return f"[{' Dot '.join(spelled_parts)}]"
    
    # Remove the text length limit - we will handle long texts by splitting into sections
        
    # Remove markdown code blocks entirely
    code_block_pattern = re.compile(r'```(?:[^`]|`(?!``)|``(?!`))*```', re.DOTALL)
    text = code_block_pattern.sub("", text)
    
    # Handle URLs with safer patterns
    text = re.sub(r'https?://[^\s<>"]{1,2048}', "[A URL is shown]", text)
    text = re.sub(r'www\.[^\s<>"]{1,2048}', "[A URL is shown]", text)
    
    # Handle Windows and Unix file paths with length limits
    text = re.sub(r'[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\){0,10}[^\\/:*?"<>|\r\n]{0,255}', "[A file path is shown]", text)
    text = re.sub(r'/(?:[a-zA-Z0-9._-]+/){0,10}[a-zA-Z0-9._-]{0,255}', "[A file path is shown]", text)
    
    # Handle email addresses - safer pattern with length limits
    text = re.sub(r'\b[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,255}\.[A-Z|a-z]{2,63}\b', "[Email address removed]", text)
    
    # Handle academic course codes and numbers
    text = re.sub(r'\b[A-Z]{2,6}\s*[-\s]*\d{2,4}(?:\s*[-\s]*\d{2,4})?\b', "[Course code]", text)
    
    # Handle excessive whitespace and formatting
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces/tabs/newlines to single space
    text = re.sub(r'[^\w\s,.!?;:\'"-]', ' ', text)  # Remove special formatting chars
    
    # Remove repeated patterns that could cause TTS issues
    text = re.sub(r'(\b\w+\b)\s+\1\s+\1', r'\1', text)  # Remove word repetition
    
    # Handle HTML tags - safer pattern with length limits
    text = re.sub(r'</?[a-zA-Z][a-zA-Z0-9]{0,20}[^>]{0,256}>', "[HTML tag is shown]", text)
    
    # Handle JSON/XML structures - safer approach with limited nesting
    def replace_data_structure(match):
        content = match.group(0)
        if len(content) > 1024:  # Limit size to process
            return "[Large data structure is shown]"
        return "[Data structure is shown]" if ('":' in content or '">' in content) else content
    
    # Use a safer approach with bounded repetition
    text = re.sub(r'[\{\[](?:[^\{\}\[\]]|\{[^\{\}\[\]]*\}|\[[^\{\}\[\]]*\]){0,100}[\}\]]', replace_data_structure, text)
    
    # Handle code syntax elements
    code_patterns = [
        r'def\s+\w{1,50}', r'class\s+\w{1,50}', r'import\s+\w{1,50}', r'function\s+\w{1,50}',
        r'var\s+\w{1,50}', r'const\s+\w{1,50}', r'let\s+\w{1,50}', r'if\s*\(', r'while\s*\(',
        r'for\s*\(', r'\{\s*\n', r'\}\s*\n', r'return\s+\w{1,50}', r'\(\)\s*\{',
        r'\([^)]{0,200}\)\s*\{', r'\}\s*else\s*\{', r';\s*\}', r'}\s*$',
    ]
    for pattern in code_patterns:
        text = re.sub(pattern, "[Code syntax is shown]", text)
    
    # Handle special character sequences - limit the repetition
    text = re.sub(r'[^\w\s,.!?;:\'"-]{4,100}', "[Special character sequence is shown]", text)
    
    # Handle hexadecimal values - limit the length
    text = re.sub(r'\b0x[0-9a-fA-F]{2,16}\b|#[0-9a-fA-F]{3,8}\b', "[A hexadecimal value is shown]", text)
    
    # Handle IP addresses - safer pattern with specific digit constraints
    ip_pattern = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
    text = ip_pattern.sub(lambda match: ip_to_words(match.group(0)), text)
    
    # Handle long numbers - limit the length
    text = re.sub(r'\b\d{6,20}\b', lambda match: f"[A {len(match.group(0))}-digit number]", text)
    
    # Remove duplicate placeholders - safer approach with bounded repetition
    text = re.sub(r'(\[.{1,50}?\])(\1){1,10}', r'\1', text)
    
    return text

# The following is only used when running the script directly
if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python cleantext.py input_file output_file")
        sys.exit(1)
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Add file size check to prevent processing extremely large files
    import os
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    if os.path.getsize(input_file) > MAX_FILE_SIZE:
        print(f"Error: Input file exceeds maximum size of {MAX_FILE_SIZE/1024/1024}MB")
        sys.exit(1)
        
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned_content = cleantext(content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"Processed {input_file} and saved to {output_file}")

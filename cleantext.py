import re

def cleantext(text):
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

    # First, handle markdown code blocks
    text = re.sub(r'```[\s\S]*?```', "[Code block is shown]", text)

    # Handle URLs
    text = re.sub(r'https?://[^\s<>"]+', "[A URL is shown]", text)
    text = re.sub(r'www\.[^\s<>"]+', "[A URL is shown]", text)

    # Handle Windows and Unix file paths
    text = re.sub(r'[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*', "[A file path is shown]", text)
    text = re.sub(r'/(?:[a-zA-Z0-9._-]+/)*[a-zA-Z0-9._-]+', "[A file path is shown]", text)

    # Handle email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[An email address is shown]", text)

    # Handle HTML tags
    text = re.sub(r'</?[a-zA-Z]+[^>]*>', "[HTML tag is shown]", text)

    # Handle JSON/XML structures
    def replace_data_structure(match):
        content = match.group(0)
        return "[Data structure is shown]" if ('":' in content or '">' in content) else content
    text = re.sub(r'[\{\[][\s\S]*?[\}\]]', replace_data_structure, text)

    # Handle code syntax elements
    code_patterns = [
        r'def\s+\w+', r'class\s+\w+', r'import\s+\w+', r'function\s+\w+',
        r'var\s+\w+', r'const\s+\w+', r'let\s+\w+', r'if\s*\(', r'while\s*\(',
        r'for\s*\(', r'\{\s*\n', r'\}\s*\n', r'return\s+\w+', r'\(\)\s*\{',
        r'\([^)]*\)\s*\{', r'\}\s*else\s*\{', r';\s*\}', r'}\s*$',
    ]
    for pattern in code_patterns:
        text = re.sub(pattern, "[Code syntax is shown]", text)

    # Handle special character sequences
    text = re.sub(r'[^\w\s,.!?;:\'"-]{4,}', "[Special character sequence is shown]", text)

    # Handle hexadecimal values
    text = re.sub(r'\b0x[0-9a-fA-F]{2,}\b|#[0-9a-fA-F]{3,6}\b', "[A hexadecimal value is shown]", text)

    # Handle IP addresses
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', lambda match: ip_to_words(match.group(0)), text)

    # Handle long numbers
    text = re.sub(r'\b\d{6,}\b', lambda match: f"[A {len(match.group(0))}-digit number]", text)

    # Remove duplicate placeholders (e.g., [Code syntax is shown][Code syntax is shown])
    text = re.sub(r'(\[.+?\])\1+', r'\1', text)

    return text

# The following is only used when running the script directly
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python cleantext.py input_file output_file")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    cleaned_content = cleantext(content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"Processed {input_file} and saved to {output_file}")

from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for
import os
from urllib.parse import quote
from testing import script

# Initialize Flask application
app = Flask(__name__)

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Handle form submission, process the input text, and generate video."""
    text_input = request.form['text_input']
    customspeed = float(request.form.get('speed', 1.0))  # Default to 1.0 if not provided
    script(text_input, customspeed)  # Pass speed to the script function
    
    # Redirect to the video output page after processing
    return redirect(url_for('output'))

@app.route('/output', methods=['GET'])
def output():
    """Stream the generated video with support for range requests."""    
    file_path = 'final.mp4'
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)
    
    if not range_header:
        # Directly return the file without chunking if no range header is present
        with open(file_path, 'rb') as f:
            return Response(f.read(), mimetype='video/mp4')
    
    # Parse range header to determine start and end bytes
    start, end = range_header.strip().lower().split('bytes=')[1].split('-')
    start = int(start)
    end = int(end) if end else file_size - 1
    length_container = [end - start + 1] 
    
    def generate_chunk():
        """Generator function to yield chunks of the video file."""
        with open(file_path, 'rb') as video_file:
            video_file.seek(start)
            chunk_size = 4096
            while length_container[0] > 0:
                chunk = video_file.read(min(chunk_size, length_container[0]))
                if not chunk:
                    break
                yield chunk
                length_container[0] -= len(chunk)
    
    # Return a streaming response with appropriate headers for range request
    return Response(stream_with_context(generate_chunk()), status=206, mimetype='video/mp4',
                    content_type='video/mp4', headers={'Content-Range': f'bytes {start}-{end}/{file_size}', 'Accept-Ranges': 'bytes'})

@app.route('/invalid_link')
def invalid_link():
    """Render the invalid link page."""
    return render_template('invalid.html')

@app.after_request
def after_request(response):
    """Add necessary headers to all responses."""
    response.headers.add('Accept-Ranges', 'bytes')
    return response

def get_chunk(byte1=None, byte2=None):
    """
    Get a specific chunk of the video file.
    
    Args:
        byte1 (int): Starting byte position
        byte2 (int): Ending byte position
    
    Returns:
        tuple: (chunk data, start position, length, total file size)
    """
    full_path = "final.mp4"
    file_size = os.stat(full_path).st_size
    start = 0
    
    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start
    with open(full_path, 'rb') as f:
        f.seek(start)
        chunk = f.read(length)
    return chunk, start, length, file_size

# Run the application in development mode with threading and debug enabled
if __name__ == '__main__':
    app.run(threaded=True, debug=True)

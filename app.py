from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for
import os
from urllib.parse import quote
from testing import script

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    text_input = request.form['text_input']
    script(text_input)
    # Now, handle the text input as needed
    # For example, redirect to the video page
    return redirect(url_for('output'))

@app.route('/output', methods=['GET'])
def output():    
    file_path = 'final.mp4'
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)

    if not range_header:
        # Directly return the file without chunking if no range header is present
        with open(file_path, 'rb') as f:
            return Response(f.read(), mimetype='video/mp4')

    start, end = range_header.strip().lower().split('bytes=')[1].split('-')
    start = int(start)
    end = int(end) if end else file_size - 1
    length_container = [end - start + 1] 

    def generate_chunk():
        with open(file_path, 'rb') as video_file:
            video_file.seek(start)
            chunk_size = 4096
            while length_container[0] > 0:
                chunk = video_file.read(min(chunk_size, length_container[0]))
                if not chunk:
                    break
                yield chunk
                length_container[0] -= len(chunk)

    return Response(stream_with_context(generate_chunk()), status=206, mimetype='video/mp4',
                    content_type='video/mp4', headers={'Content-Range': f'bytes {start}-{end}/{file_size}', 'Accept-Ranges': 'bytes'})
@app.route('/invalid_link')
def invalid_link():
    return render_template('invalid.html')

@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response


def get_chunk(byte1=None, byte2=None):
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


# this code runs the app in "development" mode which makes it easier when developing. 
# comment out for final product
if __name__ == '__main__':
    app.run(threaded=True, debug=True)


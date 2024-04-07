from flask import Flask, render_template, request, Response, stream_with_context
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/output', methods=['GET','POST'])
def output():
    file_path = 'output.mp4'
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

# this code runs the app in "development" mode which makes it easier when developing. 
# comment out for final product
if __name__ == '__main__':
    app.run(debug=True)


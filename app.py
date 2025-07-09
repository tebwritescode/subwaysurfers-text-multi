# app.py
# -------------
# Main Flask application for Subway Surfers Text-to-Video Generator.
# Handles form input, error management, and video streaming with range support.
#
# Author: [Your Name]
# Date: [Update as needed]
#
# This script provides a web interface for users to submit text, select voice and speed,
# and receive a generated video. It includes robust error handling and supports partial
# video streaming for efficient playback.

from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for, flash, send_from_directory
import os
from urllib.parse import quote
import traceback
import sys
from sub import script
from datetime import datetime
import validators

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session-based flash messages


class ScriptExecutionError(Exception):
    """
    Custom Exception for errors occurring in the sub script.
    Used to distinguish script-specific errors from general exceptions.
    """
    def __init__(self, message):
        super().__init__(message)
        self.message = message

FINAL_VIDEOS_DIR = "final_videos"
os.makedirs(FINAL_VIDEOS_DIR, exist_ok=True)

@app.route('/')
def home():
    """
    Render the home page with the input form.
    """
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    """
    Handle form submission, process the input text, and generate video.
    Validates user input, calls the external script, and manages errors.
    Redirects to the output page on success, or home page with error messages.
    """
    try:
        text_input = request.form['text_input']

        # Validate speed input (must be a float >= 0.5)
        try:
            customspeed = float(request.form.get('speed', 1.0))
            if customspeed < 0.5:  # Minimum allowed speed
                flash("Speed too slow. Minimum allowed is 0.5", "error")
                return redirect(url_for('home'))
        except ValueError:
            flash("Invalid speed value. Please enter a valid number.", "error")
            return redirect(url_for('home'))

        # Get selected voice, default to 'en_us_006' if not provided
        customvoice = str(request.form.get('voice', "en_us_006"))

        # Generate a unique filename for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Add speed and voice to filename for clarity
        safe_voice = customvoice.replace("/", "_")
        final_filename = f"{timestamp}_speed{customspeed}_voice{safe_voice}_final.mp4"
        final_path = os.path.join(FINAL_VIDEOS_DIR, final_filename)
        text_filename = f"{timestamp}_speed{customspeed}_voice{safe_voice}_final.txt"
        text_path = os.path.join(FINAL_VIDEOS_DIR, text_filename)

        # Save the original text input to a .txt file
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text_input)

        # Run external script and handle possible errors
        try:
            result = script(text_input, customspeed, customvoice, final_path)
            if result and 'error' in result:
                raise ScriptExecutionError(result['error'])
        except ScriptExecutionError as e:
            app.logger.error(f"Script execution error: {str(e)}")
            flash(f"Error in processing: {str(e)}", "error")
            return redirect(url_for('home'))
        except Exception as e:
            app.logger.error(f"Unexpected script error: {traceback.format_exc()}")
            flash(f"An internal error occurred: {str(e)}", "error")
            return redirect(url_for('home'))

        # If input was a URL, pass it to the output page for a source button
        source_url = text_input if validators.url(text_input) else None

        # On success, redirect to output page with filename, text file, and source if any
        return redirect(url_for('output', filename=final_filename, textfile=text_filename, source=source_url))

    except Exception as e:
        app.logger.error(f"Unexpected error in submit_form: {traceback.format_exc()}")
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('home'))

@app.route('/output')
def output():
    """
    Show the generated video in a player with a back arrow.
    """
    filename = request.args.get('filename')
    textfile = request.args.get('textfile')
    source = request.args.get('source')
    if not filename:
        flash("No video specified.", "error")
        return redirect(url_for('home'))
    file_path = os.path.join(FINAL_VIDEOS_DIR, filename)
    if not os.path.exists(file_path):
        flash("Video file not found. Please try again.", "error")
        return redirect(url_for('home'))
    # Defensive: check textfile exists
    textfile_path = os.path.join(FINAL_VIDEOS_DIR, textfile) if textfile else None
    if textfile and not os.path.exists(textfile_path):
        textfile = None
    return render_template('output.html', filename=filename, textfile=textfile, source=source)

@app.route('/viewtext/<textfile>')
def view_text(textfile):
    """
    View the original text used for the video.
    """
    file_path = os.path.join(FINAL_VIDEOS_DIR, textfile)
    if not os.path.exists(file_path):
        flash("Text file not found.", "error")
        return redirect(url_for('home'))
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return render_template("viewtext.html", text=content, textfile=textfile)

@app.route('/downloadtext/<textfile>')
def download_text(textfile):
    """
    Download the original text file.
    """
    return send_from_directory(FINAL_VIDEOS_DIR, textfile, as_attachment=True)

@app.route('/videos')
def videos():
    """
    Basic file browser for all generated videos.
    """
    files = sorted(os.listdir(FINAL_VIDEOS_DIR), reverse=True)
    return render_template('videos.html', files=files)

@app.route('/download/<filename>')
def download(filename):
    """
    Download a video file.
    """
    return send_from_directory(FINAL_VIDEOS_DIR, filename, as_attachment=True)

@app.route('/video/<filename>')
def serve_video(filename):
    """
    Stream a video file with range support.
    """
    file_path = os.path.join(FINAL_VIDEOS_DIR, filename)
    try:
        if not os.path.exists(file_path):
            flash("Video file not found. Please try again.", "error")
            return redirect(url_for('home'))
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range', None)
        if not range_header:
            with open(file_path, 'rb') as f:
                return Response(f.read(), mimetype='video/mp4')
        try:
            start, end = range_header.strip().lower().split('bytes=')[1].split('-')
            start = int(start)
            end = int(end) if end else file_size - 1
        except (ValueError, IndexError):
            start, end = 0, file_size - 1
        length = end - start + 1
        def generate_chunk():
            with open(file_path, 'rb') as video_file:
                video_file.seek(start)
                chunk_size = 4096
                remaining = length
                while remaining > 0:
                    chunk = video_file.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    yield chunk
                    remaining -= len(chunk)
        return Response(
            stream_with_context(generate_chunk()),
            status=206,
            mimetype='video/mp4',
            headers={
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes'
            }
        )
    except Exception as e:
        app.logger.error(f"Error in output: {traceback.format_exc()}")
        flash("Error streaming video. Please try again.", "error")
        return redirect(url_for('home'))

@app.route('/delete/<filename>', methods=['POST'])
def delete_video(filename):
    """
    Delete a video file and redirect to the videos page.
    """
    file_path = os.path.join(FINAL_VIDEOS_DIR, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            flash(f"Deleted {filename}", "info")
        else:
            flash("File not found.", "error")
    except Exception as e:
        app.logger.error(f"Error deleting video: {traceback.format_exc()}")
        flash("Error deleting video.", "error")
    return redirect(url_for('videos'))


# Global error handlers
@app.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 Not Found errors by redirecting to the home page with a flash message.
    """
    flash("Page not found", "error")
    return redirect(url_for('home'))

@app.errorhandler(500)
def server_error(e):
    """
    Handle 500 Internal Server Error by redirecting to the home page with a flash message.
    """
    flash("Internal server error. Please try again later.", "error")
    return redirect(url_for('home'))

@app.errorhandler(Exception)
def handle_unexpected_exception(e):
    """
    Catch-all handler for any unhandled exceptions, logs the error, and redirects to home.
    """
    app.logger.error(f"Unhandled exception: {traceback.format_exc()}")
    flash(f"An unexpected error occurred: {str(e)}", "error")
    return redirect(url_for('home'))


if __name__ == '__main__':
    # Configure logging for error tracking
    import logging
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    # Start the Flask app
    app.run(threaded=True, debug=False)

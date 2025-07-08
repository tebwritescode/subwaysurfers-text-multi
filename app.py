
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

from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for, flash
import os
from urllib.parse import quote
import traceback
import sys
from sub import script

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

        # Run external script and handle possible errors
        try:
            result = script(text_input, customspeed, customvoice)  # Returns error details if any
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

        # On success, redirect to output page
        return redirect(url_for('output'))

    except Exception as e:
        app.logger.error(f"Unexpected error in submit_form: {traceback.format_exc()}")
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return redirect(url_for('home'))


@app.route('/output', methods=['GET'])
def output():
    """
    Stream the generated video file (final.mp4) to the client with HTTP range request support.
    This allows for efficient video playback and seeking in the browser.
    Handles errors if the file is missing or streaming fails.
    """
    file_path = 'final.mp4'

    try:
        # Check if the video file exists
        if not os.path.exists(file_path):
            flash("Video file not found. Please try again.", "error")
            return redirect(url_for('home'))

        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range', None)

        # If no range header, serve the entire file
        if not range_header:
            with open(file_path, 'rb') as f:
                return Response(f.read(), mimetype='video/mp4')

        # Parse the range header for partial content
        try:
            start, end = range_header.strip().lower().split('bytes=')[1].split('-')
            start = int(start)
            end = int(end) if end else file_size - 1
        except (ValueError, IndexError):
            start, end = 0, file_size - 1  # Serve the full file if parsing fails

        length = end - start + 1

        def generate_chunk():
            """
            Generator to yield video file chunks for streaming.
            """
            try:
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
            except Exception as e:
                app.logger.error(f"Error generating video chunk: {str(e)}")

        # Return partial content response with appropriate headers
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

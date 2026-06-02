# app.py
# -----------------------------------------------------------------------------
# Flask web application for the Subway Surfers Text-to-Video Generator.
#
# Provides a web UI to submit text or an article URL, choose a TTS backend and
# voice, and generate a captioned gameplay video. Generation runs in a
# background thread with real-time progress over Server-Sent Events.
# -----------------------------------------------------------------------------

import json
import logging
import os
import queue
import sys
import threading
import time
import traceback
from datetime import datetime

import validators
from dotenv import load_dotenv
from flask import (Flask, Response, redirect, render_template, request,
                   send_from_directory, stream_with_context, url_for, flash)
from werkzeug.utils import secure_filename

# Load .env before importing modules that read configuration at import time.
load_dotenv()

from sub import script  # noqa: E402
from text_to_speech import available_backends, list_voices
from version import __version__

app = Flask(__name__)
app.secret_key = os.urandom(24)

# session_id -> queue of progress updates
progress_queues = {}

FINAL_VIDEOS_DIR = "final_videos"
os.makedirs(FINAL_VIDEOS_DIR, exist_ok=True)


def safe_video_path(filename):
    """
    Resolve ``filename`` to a path inside FINAL_VIDEOS_DIR, or None if the name
    is unsafe. Guards every file route against path traversal.
    """
    name = secure_filename(filename or "")
    if not name:
        return None
    base = os.path.realpath(FINAL_VIDEOS_DIR)
    full = os.path.realpath(os.path.join(base, name))
    if os.path.commonpath([base, full]) != base:
        return None
    return full


# --- API ---------------------------------------------------------------------

@app.route('/api/voices')
def get_voices():
    """Return the available voices for a TTS backend as JSON."""
    backend = request.args.get('backend')
    try:
        return list_voices(backend)
    except Exception as exc:
        return {"voices": [], "error": str(exc)}


# --- Pages -------------------------------------------------------------------

@app.route('/')
def home():
    """Render the generation form with TTS backends and the default voice list."""
    backends = available_backends()
    default_backend = next((b['id'] for b in backends if b['is_default']), None)
    try:
        voices_result = list_voices(default_backend)
    except Exception as exc:
        voices_result = {"voices": [], "error": str(exc)}
    return render_template(
        'index.html',
        version=__version__,
        backends=backends,
        default_backend=default_backend,
        voices=voices_result.get("voices", []),
        voices_error=voices_result.get("error"),
    )


@app.route('/progress/<session_id>')
def progress_stream(session_id):
    """Server-Sent Events stream of generation progress for a session."""
    def generate_progress():
        if session_id not in progress_queues:
            yield f"data: {json.dumps({'error': 'Invalid session'})}\n\n"
            return
        progress_queue = progress_queues[session_id]
        while True:
            try:
                progress_data = progress_queue.get(timeout=30)
                if progress_data is None:
                    break
                yield f"data: {json.dumps(progress_data)}\n\n"
            except queue.Empty:
                yield f"data: {json.dumps({'heartbeat': True})}\n\n"
            except Exception:
                break
        progress_queues.pop(session_id, None)

    return Response(generate_progress(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
    })


@app.route('/submit-form', methods=['POST'])
def submit_form():
    """Validate input and start background video generation."""
    try:
        text_input = request.form['text_input']

        try:
            customspeed = float(request.form.get('speed', 1.0))
            if customspeed < 0.25:
                flash("Speed too slow. Minimum allowed is 0.25", "error")
                return redirect(url_for('home'))
        except ValueError:
            flash("Invalid speed value. Please enter a valid number.", "error")
            return redirect(url_for('home'))

        backend = request.form.get('backend') or None
        customvoice = str(request.form.get('voice', "default"))

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_voice = customvoice.replace("/", "_")
        session_id = f"{timestamp}_{customspeed}_{safe_voice}"
        final_filename = f"{timestamp}_speed{customspeed}_voice{safe_voice}_final.mp4"
        final_path = os.path.join(FINAL_VIDEOS_DIR, final_filename)
        text_filename = f"{timestamp}_speed{customspeed}_voice{safe_voice}_final.txt"
        text_path = os.path.join(FINAL_VIDEOS_DIR, text_filename)

        with open(text_path, "w", encoding="utf-8") as handle:
            handle.write(text_input)

        progress_queue = queue.Queue()
        progress_queues[session_id] = progress_queue

        def run_generation():
            try:
                result = script(text_input, customspeed, customvoice, final_path,
                                progress_queue, backend=backend)
                if result and 'error' in result:
                    progress_queue.put({'error': result['error'], 'step': 'error'})
                else:
                    progress_queue.put({'progress': 100, 'step': 'completed',
                                        'message': 'Video generation completed!'})
            except Exception as exc:
                app.logger.error("Generation error: %s", traceback.format_exc())
                progress_queue.put({'error': f"Processing error: {exc}", 'step': 'error'})
            finally:
                progress_queue.put(None)

        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()

        source_url = text_input if validators.url(text_input) else None
        return render_template('progress.html',
                               session_id=session_id,
                               final_filename=final_filename,
                               textfile=text_filename,
                               source=source_url,
                               version=__version__)
    except Exception as exc:
        app.logger.error("submit_form error: %s", traceback.format_exc())
        flash(f"An unexpected error occurred: {exc}", "error")
        return redirect(url_for('home'))


@app.route('/output')
def output():
    """Show a generated video in the player."""
    filename = request.args.get('filename')
    textfile = request.args.get('textfile')
    source = request.args.get('source')
    file_path = safe_video_path(filename)
    if not file_path or not os.path.exists(file_path):
        flash("Video file not found. Please try again.", "error")
        return redirect(url_for('home'))
    textfile_path = safe_video_path(textfile) if textfile else None
    if textfile and (not textfile_path or not os.path.exists(textfile_path)):
        textfile = None
    return render_template('output.html', filename=filename, textfile=textfile,
                           source=source, version=__version__)


@app.route('/viewtext/<textfile>')
def view_text(textfile):
    """View the original input text for a video."""
    file_path = safe_video_path(textfile)
    if not file_path or not os.path.exists(file_path):
        flash("Text file not found.", "error")
        return redirect(url_for('home'))
    with open(file_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    return render_template("viewtext.html", text=content, textfile=textfile, version=__version__)


@app.route('/downloadtext/<textfile>')
def download_text(textfile):
    """Download the original input text file."""
    return send_from_directory(FINAL_VIDEOS_DIR, textfile, as_attachment=True)


@app.route('/videos')
def videos():
    """List all generated videos (the management page)."""
    files = sorted(os.listdir(FINAL_VIDEOS_DIR), reverse=True)
    return render_template('videos.html', files=files, version=__version__)


@app.route('/download/<filename>')
def download(filename):
    """Download a generated video."""
    return send_from_directory(FINAL_VIDEOS_DIR, filename, as_attachment=True)


@app.route('/video/<filename>')
def serve_video(filename):
    """Stream a video file with HTTP range support."""
    file_path = safe_video_path(filename)
    try:
        if not file_path or not os.path.exists(file_path):
            flash("Video file not found. Please try again.", "error")
            return redirect(url_for('home'))
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range', None)
        if not range_header:
            with open(file_path, 'rb') as handle:
                return Response(handle.read(), mimetype='video/mp4')
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
                remaining = length
                while remaining > 0:
                    chunk = video_file.read(min(4096, remaining))
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
                'Accept-Ranges': 'bytes',
            },
        )
    except Exception:
        app.logger.error("serve_video error: %s", traceback.format_exc())
        flash("Error streaming video. Please try again.", "error")
        return redirect(url_for('home'))


@app.route('/delete/<filename>', methods=['POST'])
def delete_video(filename):
    """Delete a generated video (and is referenced by the management page)."""
    file_path = safe_video_path(filename)
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            flash(f"Deleted {secure_filename(filename)}", "info")
        else:
            flash("File not found.", "error")
    except Exception:
        app.logger.error("delete_video error: %s", traceback.format_exc())
        flash("Error deleting video.", "error")
    return redirect(url_for('videos'))


# --- Error handlers ----------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    return redirect(url_for('home')), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Internal server error: %s", error)
    flash("An internal server error occurred. Please try again.", "error")
    return redirect(url_for('home')), 500


@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error("Unhandled exception: %s", traceback.format_exc())
    flash(f"An unexpected error occurred: {error}", "error")
    return redirect(url_for('home')), 500


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True, debug=False)

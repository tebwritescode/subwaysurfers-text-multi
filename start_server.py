#!/usr/bin/env python3
"""
Auto-restarting Flask server for the Subway Surfers Text-to-Video application.
This script ensures the application restarts automatically if it crashes.
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('server.log')
    ]
)
logger = logging.getLogger(__name__)

class FlaskServerManager:
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 5
        self.running = True
        
        # Get environment variables
        self.host = os.getenv('FLASK_HOST', '127.0.0.1')
        self.port = os.getenv('FLASK_PORT', '5001')
        self.debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
        
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning("Process didn't terminate gracefully, killing...")
                self.process.kill()
        sys.exit(0)
    
    def check_dependencies(self):
        """Check if required files exist."""
        required_files = [
            'app.py',
            'sub.py',
            'version.py',
            'static',
            'templates',
            'static/vosk-model-en-us-0.22'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.error(f"Missing required files/directories: {missing_files}")
            return False
        
        # Check for at least one video file
        video_files = list(Path('static').glob('*.mp4'))
        if not video_files:
            logger.error("No video files found in static/ directory")
            return False
        
        logger.info(f"Found {len(video_files)} video files")
        return True
    
    def start_flask_server(self):
        """Start the Flask server process."""
        env = os.environ.copy()
        env.update({
            'FLASK_APP': 'app.py',
            'FLASK_ENV': 'development' if self.debug else 'production',
            'FLASK_DEBUG': '1' if self.debug else '0',
            'PYTHONUNBUFFERED': '1'
        })
        
        cmd = [
            sys.executable, '-m', 'flask', 'run',
            '--host', self.host,
            '--port', self.port
        ]
        
        logger.info(f"Starting Flask server: {' '.join(cmd)}")
        return subprocess.Popen(cmd, env=env)
    
    def run(self):
        """Main run loop with auto-restart functionality."""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("Starting Flask Server Manager...")
        
        # Check dependencies
        if not self.check_dependencies():
            logger.error("Dependency check failed. Exiting.")
            return 1
        
        while self.running and self.restart_count < self.max_restarts:
            try:
                logger.info(f"Attempt {self.restart_count + 1}/{self.max_restarts}")
                
                # Start Flask server
                self.process = self.start_flask_server()
                logger.info(f"Flask server started with PID {self.process.pid}")
                
                # Wait for process to complete or crash
                return_code = self.process.wait()
                
                if not self.running:
                    break
                
                if return_code != 0:
                    self.restart_count += 1
                    logger.error(f"Flask server crashed with return code {return_code}")
                    
                    if self.restart_count < self.max_restarts:
                        logger.info(f"Restarting in {self.restart_delay} seconds...")
                        time.sleep(self.restart_delay)
                    else:
                        logger.error("Maximum restart attempts reached. Exiting.")
                        break
                else:
                    logger.info("Flask server exited normally")
                    break
                    
            except Exception as e:
                logger.error(f"Error managing Flask server: {e}")
                if self.restart_count < self.max_restarts:
                    self.restart_count += 1
                    time.sleep(self.restart_delay)
                else:
                    break
        
        logger.info("Flask Server Manager shutting down")
        return 0

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    manager = FlaskServerManager()
    sys.exit(manager.run())
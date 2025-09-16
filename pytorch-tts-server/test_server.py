#!/usr/bin/env python3
"""
Minimal test server to verify FastAPI works
"""
from fastapi import FastAPI
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Test TTS Server")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Test server running"}

@app.get("/")
async def root():
    return {"message": "Test TTS Server is running"}

if __name__ == "__main__":
    logger.info("Starting test server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
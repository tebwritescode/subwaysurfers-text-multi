#!/bin/bash
# concat.sh - Merge video and audio files using FFmpeg
# Usage: ./concat.sh <input_video> <input_audio> <intermediate_output> <final_output>

set -e  # Exit on error

# Check if all parameters are provided
if [ "$#" -ne 4 ]; then
    echo "Error: Incorrect number of parameters"
    echo "Usage: $0 <input_video> <input_audio> <intermediate_output> <final_output>"
    exit 1
fi

INPUT_VIDEO="$1"
INPUT_AUDIO="$2"
INTERMEDIATE_OUTPUT="$3"
FINAL_OUTPUT="$4"

echo "Starting video/audio merge process..."
echo "Input video: $INPUT_VIDEO"
echo "Input audio: $INPUT_AUDIO"
echo "Final output: $FINAL_OUTPUT"

# First pass: Merge video and audio
echo "Pass 1: Merging video and audio..."
ffmpeg -i "$INPUT_VIDEO" -i "$INPUT_AUDIO" -c copy -map 0:v:0 -map 1:a:0 "$INTERMEDIATE_OUTPUT" -shortest -preset slow -y

# Check if intermediate file was created
if [ ! -f "$INTERMEDIATE_OUTPUT" ]; then
    echo "Error: Intermediate file was not created"
    exit 1
fi

# Second pass: Re-encode to ensure compatibility
echo "Pass 2: Re-encoding for compatibility..."
ffmpeg -i "$INTERMEDIATE_OUTPUT" -vcodec h264 -acodec aac "$FINAL_OUTPUT" -preset slow -y

# Check if final file was created
if [ ! -f "$FINAL_OUTPUT" ]; then
    echo "Error: Final file was not created"
    exit 1
fi

echo "Video merge completed successfully!"

# Cleanup intermediate file
rm -f "$INTERMEDIATE_OUTPUT"

# For GPU acceleration, uncomment these lines and comment out the above ffmpeg commands:
# ffmpeg -i "$INPUT_VIDEO" -i "$INPUT_AUDIO" -c:v h264_nvenc -preset slow -b:v 5M -c:a copy -map 0:v:0 -map 1:a:0 -shortest "$INTERMEDIATE_OUTPUT" -y
# ffmpeg -i "$INTERMEDIATE_OUTPUT" -c:v h264_nvenc -c:a aac "$FINAL_OUTPUT" -y
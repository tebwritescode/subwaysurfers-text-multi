ffmpeg -i $1 -i $2 -c copy -map 0:v:0 -map 1:a:0 $3 -shortest -preset slow
ffmpeg -i $3 -vcodec h264 -acodec aac $4 -preset slow

# Replace above commands with below commands to use NVIDIA GPU
# ffmpeg -i "$1" -i "$2" -c:v h264_nvenc -preset slow -b:v 5M -c:a copy -map 0:v:0 -map 1:a:0 -shortest "$3"
# ffmpeg -i "$3" -c:v h264_nvenc -c:a aac "$4"

ffmpeg -i $1 -i $2 -c copy -map 0:v:0 -map 1:a:0 $3 -shortest

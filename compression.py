from moviepy.editor import VideoFileClip

def compress_video(input_path, output_path, bitrate='1000k'):
    clip = VideoFileClip(input_path)
    clip.write_videofile(output_path, bitrate=bitrate)
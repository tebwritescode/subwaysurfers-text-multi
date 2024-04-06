import cv2

# Load your video file
video_path = "subsurf.mp4"
cap = cv2.VideoCapture(video_path)

# Get video properties
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
output_video = cv2.VideoWriter('output_video.mp4', fourcc, fps, (width, height))

# Define the text properties
font = cv2.FONT_HERSHEY_SIMPLEX
text_position = (360, 360)
font_scale = 1
font_color = (255, 255, 255)
thickness = 2

# Initialize variables for timing
frame_count = 0
text_change_interval = 10  # Change text every 10 frames
current_text = ""  # Current text to be displayed

# Read lines from the file
with open("demofile.txt", "r") as file:
    lines = file.readlines()  # Read all lines from the file

while(cap.isOpened()):
    ret, frame = cap.read()
    if not ret:
        break
    
    # Update the text every text_change_interval frames
    if frame_count % (text_change_interval * fps) == 0:
        # Determine the index of the current line
        line_index = frame_count // (text_change_interval * fps) % len(lines)
        current_text = lines[line_index].strip()  # Get the current line from the list of lines and remove leading/trailing whitespaces
    
    # Add text to the frame
    cv2.putText(frame, current_text, text_position, font, font_scale, font_color, thickness, cv2.LINE_AA)
    
    # Write the frame to the output video
    output_video.write(frame)
    
    frame_count += 1

# Release the video capture and writer objects
cap.release()
output_video.release()
cv2.destroyAllWindows()

import cv2
import os
from pathlib import Path

# Parameters
input_dir = r"E:\netholabs_videos"               # Folder with your videos
output_dir = r"E:\netholabs_videos\frames"       # Folder to save extracted frames
N = 75                                      # Extract every N-th frame

os.makedirs(output_dir, exist_ok=True)

# Iterate through all video files in the directory
video_extensions = [".mp4", ".avi", ".mov", ".mkv"]
for video_path in Path(input_dir).glob("*"):
    if video_path.suffix.lower() not in video_extensions:
        continue

    cap = cv2.VideoCapture(str(video_path))
    frame_count = 0

    if not cap.isOpened():
        print(f"Failed to open {video_path}")
        continue

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % N == 0:
            filename = f"{video_path.stem}_frame{frame_count:06d}.png"
            save_path = Path(output_dir) / filename
            cv2.imwrite(str(save_path), frame)

        frame_count += 1

    cap.release()
    print(f"Finished extracting from {video_path.name}")
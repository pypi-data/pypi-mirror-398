#!/usr/bin/env python3
"""
Join PNG frames into a video at 10 fps using ffmpeg.
"""

import subprocess
import sys
from pathlib import Path

def join_frames_to_video(frames_dir="output/frames", output_video="output/network_video_30fps.mp4", fps=30):
    """Join PNG frames into a video using ffmpeg."""
    
    frames_path = Path(frames_dir)
    output_path = Path(output_video)
    
    # Check if frames directory exists
    if not frames_path.exists():
        print(f"Error: Frames directory '{frames_dir}' does not exist!")
        return False
    
    # Check if there are any PNG files
    png_files = list(frames_path.glob("*.png"))
    if not png_files:
        print(f"Error: No PNG files found in '{frames_dir}'!")
        return False
    
    print(f"Found {len(png_files)} PNG files")
    print(f"Creating video at {fps} fps...")
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build ffmpeg command with higher quality settings
    cmd = [
        "ffmpeg",
        "-y",  # Overwrite output file
        "-framerate", str(fps),
        "-i", str(frames_path / "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "slow",  # Better compression
        "-crf", "18",  # High quality (lower = better quality)
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        # Run ffmpeg
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, check=True)
        print("✓ Video created successfully!")
        print(f"Output: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error creating video: {e}")
        print(f"stderr: {e.stderr.decode()}")
        return False
    except FileNotFoundError:
        print("✗ Error: ffmpeg not found! Please install ffmpeg.")
        print("Download from: https://ffmpeg.org/download.html")
        return False

if __name__ == "__main__":
    # Default parameters
    frames_dir = "output/frames"
    output_video = "output/network_video_30fps.mp4"
    fps = 30
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        frames_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_video = sys.argv[2]
    if len(sys.argv) > 3:
        fps = int(sys.argv[3])
    
    print(f"Joining frames from: {frames_dir}")
    print(f"Output video: {output_video}")
    print(f"Frame rate: {fps} fps")
    print("-" * 50)
    
    success = join_frames_to_video(frames_dir, output_video, fps)
    
    if success:
        print("\n✓ Video creation completed!")
    else:
        print("\n✗ Video creation failed!")
        sys.exit(1)

import os
import random
import subprocess
from pathlib import Path

def get_total_frames(video_path):
    """Return total number of frames in a video using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-count_frames",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=nokey=1:noprint_wrappers=1",
        str(video_path)
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0

def extract_random_frames(video_path, output_dir, n=10):
    """Extract N random frames from a single video."""
    total_frames = get_total_frames(video_path)
    if total_frames == 0:
        print(f"⚠️ Skipping {video_path.name}: Could not get frame count.")
        return

    if n > total_frames:
        n = total_frames

    # Randomly select N unique frame numbers (1-indexed for ffmpeg)
    frame_indices = sorted(random.sample(range(1, total_frames + 1), n))
    frame_expr = "+".join([f"eq(n,{i-1})" for i in frame_indices])

    video_name = video_path.stem
    save_dir = Path(output_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    output_pattern = save_dir / f"{video_name}_frame%06d.png"

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"select='{frame_expr}',setpts=N/FRAME_RATE/TB",
        "-vsync", "vfr",
        str(output_pattern),
        "-hide_banner", "-loglevel", "error"
    ]

    print(f"🎞️ Extracting {n} random frames from: {video_path.name}")
    subprocess.run(cmd, check=True)


def extract_random_frames_from_all(root_dir, output_dir, n=10):
    """Recursively extract N random frames from each video."""
    root_dir = Path(root_dir)
    video_exts = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"}

    for video_path in root_dir.rglob("*"):
        if video_path.suffix.lower() in video_exts:
            extract_random_frames(video_path, output_dir, n)

    print("✅ Random frame extraction complete.")

extract_random_frames_from_all(root_dir=r"E:\netholabs_videos\3d_track_1101025\rotated", output_dir=r"E:\netholabs_videos\3d_track_1101025\imgs", n=100)

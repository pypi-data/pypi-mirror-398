import os
import subprocess
from pathlib import Path


def rotate_videos_180(in_dir, out_dir, overwrite=True):
    in_dir = Path(in_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for file in in_dir.glob("*.*"):
        if file.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv", ".h264"]:
            out_file = out_dir / f"{file.stem}_rotated{file.suffix}"
            cmd = [
                "ffmpeg",
                "-i", str(file),
                "-vf", "hflip,vflip",  # reliable 180° rotation
                "-c:a", "copy",        # keep audio
            ]
            if overwrite:
                cmd.append("-y")
            cmd.append(str(out_file))

            print("Running:", " ".join(cmd))
            subprocess.run(cmd, check=True)


rotate_videos_180(r"E:\netholabs_videos\3d_track_1101025\mp4", r"E:\netholabs_videos\3d_track_1101025\rotated")
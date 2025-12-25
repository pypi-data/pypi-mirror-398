import os
import glob
import numpy as np
from typing import Union
import subprocess
import time

H265 = '.h264'

def change_fps(data_dir: Union[str, os.PathLike],
               save_dir: Union[str, os.PathLike],
               fps: int = 1,
               gpu: bool = False):

    """
    Lossless MP4 convertion and reducion of sampling frequency of H265 input videos.

    :example:
    >>> DATA_DIR = r"D:\netholabs\videos"
    >>> SAVE_DIR = r"D:\netholabs\out"
    >>> change_fps(data_dir=DATA_DIR, save_dir=SAVE_DIR, fps=1)

    .. notes:
       Input videos: 14 videos, 120 FPS H265, 1280x720, 240MBish each, 3.5min
       GPU: Total time: 48s, Video mean: 3.484s, Video Stdev: 0.126s.
       CPU: Total time: 14.85s, Video mean: 1.061s, Video Stdev: 0.0337s.
    """

    timers = []
    file_paths = glob.glob(data_dir + f'/*{H265}')
    for cnt, file_path in enumerate(file_paths):
        video_start_time = time.time()
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        print(f'Converting {file_name} to {fps} FPS mp4 ({cnt+1}/{len(file_paths)})..')
        save_path = os.path.join(save_dir, f"{file_name}.h264")
        if not gpu:
            #cmd = f'ffmpeg -i "{file_path}" -vf "fps={fps}" -c:v libx264 -preset ultrafast -crf 0 -pix_fmt yuv420p "{save_path}" -loglevel error -stats -hide_banner -y'
           # cmd = f'ffmpeg -i "{file_path}" -vf "fps={fps}" -c:v rawvideo -pix_fmt rgb24 "{save_path}" -loglevel error -stats -hide_banner -y'
            cmd = f'ffmpeg -i "{file_path}" -vf "fps={fps}" -c:v rawvideo -pix_fmt rgb24 "{save_path}" -loglevel error -stats -hide_banner -y'

        else:
            cmd = f'ffmpeg -hwaccel auto -i "{file_path}" -vf "fps={fps}" -c:v h264_nvenc -preset p1 -qp 0 -pix_fmt yuv420p "{save_path}" -loglevel error -stats -hide_banner -y'
        subprocess.run(cmd, shell=True, check=True)
        timers.append(time.time()-video_start_time)
    print(np.sum(timers), np.mean(timers), np.std(timers))


DATA_DIR = r'D:\netholabs\videos'
SAVE_DIR = r"D:\netholabs\out_2"
change_fps(data_dir=DATA_DIR, save_dir=SAVE_DIR, fps=1, gpu=False)




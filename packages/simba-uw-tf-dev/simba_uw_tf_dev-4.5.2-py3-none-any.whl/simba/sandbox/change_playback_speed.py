from typing import Union, Optional
import os
from simba.utils.checks import check_float, check_if_dir_exists, check_int, check_ffmpeg_available
from simba.utils.read_write import get_fn_ext, get_video_meta_data
from simba.utils.lookups import quality_pct_to_crf
import subprocess

def change_playback_speed(video_path: Union[str, os.PathLike],
                          speed: float,
                          save_path: Optional[Union[str, os.PathLike]] = None,
                          quality: int = 60,
                          codec: str = 'libx264'):

    """

    :param video_path:
    :param speed:
    :param save_path:
    :param quality:
    :param codec:
    :return:

    :example:
    >>> change_playback_speed(video_path=r"C:\Users\sroni\OneDrive\Desktop\sam_clip_fps_50_cropped_1_sam_clip_fps_50_cropped_concat_shorten.mp4", speed=1.5)
    """

    check_ffmpeg_available(raise_error=True)
    check_float(name=f'{change_playback_speed.__name__} speed', value=speed, min_value=0.001, max_value=100, raise_error=True)
    check_int(name=f'{change_playback_speed.__name__} quality', value=quality, min_value=1, max_value=100, raise_error=True)
    _ = get_video_meta_data(video_path=video_path)
    quality_code = quality_pct_to_crf(pct=quality)
    if save_path is not None:
        check_if_dir_exists(in_dir=os.path.dirname(save_path), source=f'{change_playback_speed.__name__} save_path')
    else:
        dir, video_name, ext = get_fn_ext(filepath=video_path)
        save_path = os.path.join(dir, f'{video_name}_playback_speed{ext}')

    video_pts = 1.0 / speed
    cmd = f'ffmpeg -i "{video_path}" -vf "setpts={video_pts:.6f}*PTS" -an -c:v {codec} -crf {quality_code} "{save_path}" -hide_banner -loglevel error -stats -y'
    subprocess.call(cmd, shell=True)



__author__ = "Simon Nilsson"
import os
from typing import Optional, Tuple, Union
import numpy as np

from simba.utils.checks import check_file_exist_and_readable, check_int
from simba.utils.read_write import get_video_meta_data, read_frm_of_video


def find_closest_readable_frame(video_path: Union[str, os.PathLike],
                                target_frame: int,
                                max_search_range: int = 100) -> Tuple[Optional[np.ndarray], Optional[int]]:
    """
    Finds the closest readable frame to a target frame index.

    This function attempts to read the target frame from a video. If the target frame cannot be read
    (e.g., due to corruption or encoding issues), it searches nearby frames in both directions to find
    the closest readable frame.

    :param Union[str, os.PathLike] video_path: Path to video file.
    :param int target_frame: Target frame index to read (0-based).
    :param int max_search_range: Maximum number of frames to search in each direction from target. Default: 100.
    :return: Tuple of (frame array, actual frame index) or (None, None) if no readable frame found.
    :rtype: Tuple[Optional[np.ndarray], Optional[int]]

    :example:
    >>> frame, actual_idx = find_closest_readable_frame(video_path='video.mp4', target_frame=10810)
    >>> if frame is not None:
    >>>     print(f"Read frame {actual_idx} (target was 10810, offset: {actual_idx - 10810})")
    """
    
    check_file_exist_and_readable(file_path=video_path)
    check_int(name='target_frame', value=target_frame, min_value=0)
    check_int(name='max_search_range', value=max_search_range, min_value=1)

    video_meta = get_video_meta_data(video_path=video_path)
    target_frame = max(0, min(target_frame, video_meta['frame_count'] - 1))

    img = read_frm_of_video(video_path=video_path, frame_index=target_frame, raise_error=False)
    if img is not None:
        return img, target_frame

    for offset in range(1, max_search_range + 1):
        test_frame = target_frame - offset
        if test_frame >= 0:
            img = read_frm_of_video(video_path=video_path, frame_index=test_frame, raise_error=False)
            if img is not None:
                return img, test_frame

        test_frame = target_frame + offset
        if test_frame < video_meta['frame_count']:
            img = read_frm_of_video(video_path=video_path, frame_index=test_frame, raise_error=False)
            if img is not None:
                return img, test_frame

    return None, None

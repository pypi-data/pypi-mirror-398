

import functools
import gc
import glob
import multiprocessing
import os
import platform
import shutil
import subprocess
import time
from copy import deepcopy
from datetime import datetime
from tkinter import *
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pandas as pd
from PIL import Image, ImageTk
from shapely.affinity import scale
from shapely.geometry import MultiPolygon, Polygon
from skimage.color import label2rgb
from skimage.segmentation import slic

try:
    from typing import Literal
except:
    from typing_extensions import Literal

from simba.mixins.config_reader import ConfigReader
from simba.mixins.image_mixin import ImageMixin
from simba.utils.checks import (check_ffmpeg_available,
                                check_file_exist_and_readable, check_float,
                                check_if_dir_exists,
                                check_if_filepath_list_is_empty,
                                check_if_string_value_is_valid_video_timestamp,
                                check_if_valid_img, check_instance, check_int,
                                check_nvidea_gpu_available, check_str,
                                check_that_hhmmss_start_is_before_end,
                                check_valid_boolean, check_valid_lst,
                                check_valid_tuple)
from simba.utils.data import find_frame_numbers_from_time_stamp
from simba.utils.enums import ConfigKey, Defaults, Formats, Options, Paths
from simba.utils.errors import (CountError, DirectoryExistError,
                                FFMPEGCodecGPUError, FFMPEGNotFoundError,
                                FileExistError, FrameRangeError,
                                InvalidFileTypeError, InvalidInputError,
                                InvalidVideoFileError, NoDataError,
                                NoFilesFoundError, NotDirectoryError,
                                ResolutionError, SimBAGPUError)
from simba.utils.lookups import (get_ffmpeg_crossfade_methods, get_fonts,
                                 get_named_colors, percent_to_crf_lookup,
                                 percent_to_qv_lk,
                                 video_quality_to_preset_lookup)
from simba.utils.printing import SimbaTimer, stdout_success
from simba.utils.read_write import (
    check_if_hhmmss_timestamp_is_valid_part_of_video,
    concatenate_videos_in_folder, create_directory,
    find_all_videos_in_directory, find_core_cnt,
    find_files_of_filetypes_in_directory, get_fn_ext, get_video_meta_data,
    read_config_entry, read_config_file, read_frm_of_video,
    read_img_batch_from_video_gpu, recursive_file_search, read_img)
from simba.utils.warnings import (CropWarning, FFMpegCodecWarning,
                                  FileExistWarning, FrameRangeWarning,
                                  GPUToolsWarning, InValidUserInputWarning,
                                  SameInputAndOutputWarning)
from simba.video_processors.async_frame_reader import AsyncVideoFrameReader, get_async_frame_batch
from simba.video_processors.extract_frames import video_to_frames
from simba.video_processors.roi_selector import ROISelector
from simba.video_processors.roi_selector_circle import ROISelectorCircle
from simba.video_processors.roi_selector_polygon import ROISelectorPolygon
from simba.video_processors.video_processing import create_average_frm
#try:
import cupy as cp
#except:
#import numpy as cp


def video_bg_subtraction_async(video_path: Union[str, os.PathLike],
                               bg_video_path: Union[str, os.PathLike] = None,
                               bg_start_frm: Optional[int] = None,
                               bg_end_frm: Optional[int] = None,
                               bg_start_time: Optional[str] = None,
                               bg_end_time: Optional[str] = None,
                               avg_frm: Optional[Union[np.ndarray, str, os.PathLike]] = None,
                               bg_color: Tuple[int, int, int] = (0, 0, 0),
                               fg_color: Optional[Tuple[int, int, int]] = None,
                               save_path: Optional[Union[str, os.PathLike]] = None,
                               batch_size: int = 500,
                               verbose: bool = True,
                               gpu: bool = False,
                               threshold: Optional[int] = 50,
                               method: str = 'absolute',
                               closing_kernel_size: Optional[Tuple[int, int]] = None,
                               closing_iterations: int = 3,
                               opening_kernel_size: Optional[Tuple[int, int]] = None,
                               opening_iterations: int = 3) -> None:

    """
    Subtract the background from a video using multiprocessing.

    .. video:: _static/img/video_bg_substraction_mp.webm
       :width: 900
       :autoplay:
       :loop:

    .. video:: _static/img/bg_remover_example_3.webm
       :width: 900
       :autoplay:
       :loop:

    .. video:: _static/img/bg_remover_example_4.webm
       :width: 900
       :autoplay:
       :loop:

    .. note::
       If  ``bg_video_path`` is passed, that video will be used to parse the background. If None, ``video_path`` will be use to parse background.
       Either pass ``start_frm`` and ``end_frm`` OR ``start_time`` and ``end_time`` OR pass all four arguments as None.
       Those two arguments will be used to slice the background video, and the sliced part is used to parse the background.

       For example, in the scenario where there is **no** animal in the ``video_path`` video for the first 20s, then the first 20s can be used to parse the background.
       In this scenario, ``bg_video_path`` can be passed as ``None`` and bg_start_time and bg_end_time can be ``00:00:00`` and ``00:00:20``, repectively.

       In the scenario where there **is** animal(s) in the entire ``video_path`` video, pass ``bg_video_path`` as a path to a video recording the arena without the animals.

    .. seealso::
        For single core alternative, see :func:`~simba.video_processors.video_processing.video_bg_subtraction`.
        For GPU based alternative, see :func:`~simba.data_processors.cuda.image.bg_subtraction_cuda` or :func:`~simba.data_processors.cuda.image.bg_subtraction_cupy`.

    :param Union[str, os.PathLike] video_path: The path to the video to remove the background from.
    :param Optional[np.ndarray] avg_frm: The average frame to use to compute the background. If None is passed, then the average frame will be computed.
    :param Optional[Union[str, os.PathLike]] bg_video_path: Path to the video which contains a segment with the background only. If None, then ``video_path`` will be used.
    :param Optional[int] bg_start_frm: The first frame in the background video to use when creating a representative background image. Default: None.
    :param Optional[int] bg_end_frm: The last frame in the background video to use when creating a representative background image. Default: None.
    :param Optional[str] bg_start_time: The start timestamp in `HH:MM:SS` format in the background video to use to create a representative background image. Default: None.
    :param Optional[str] bg_end_time: The end timestamp in `HH:MM:SS` format in the background video to use to create a representative background image. Default: None.
    :param Optional[str] bg_end_time: The end timestamp in `HH:MM:SS` format in the background video to use to create a representative background image. Default: None.
    :param Optional[Tuple[int, int, int]] bg_color: The RGB color of the moving objects in the output video. Defaults to None, which represents the original colors of the moving objects.
    :param Optional[Union[str, os.PathLike]] save_path: The patch to where to save the output video where the background is removed. If None, saves the output video in the same directory as the input video with the ``_bg_subtracted`` suffix. Default: None.
    :param Optional[int] core_cnt: The number of cores to use. Defaults to -1 representing all available cores.
    :param Optional[int] threshold: Value between 0-255 representing the difference threshold between the average frame subtracted from each frame. Higher values and more pixels will be considered background. Default: 50.
    :return: None.

    :example:
    >>> video_bg_subtraction_mp(video_path='/Users/simon/Downloads/1_LH.mp4', bg_start_time='00:00:00', bg_end_time='00:00:10', bg_color=(0, 0, 0), fg_color=(255, 255, 255))
    """

    timer = SimbaTimer(start=True)
    check_file_exist_and_readable(file_path=video_path)
    check_int(name=f'{video_bg_subtraction_async.__name__} threshold', value=threshold, min_value=1, max_value=255)
    check_str(name='method', value=method, options=['absolute', 'light', 'dark'], raise_error=True)
    if bg_video_path is None: bg_video_path = deepcopy(video_path)
    video_meta_data = get_video_meta_data(video_path=video_path)
    dir, video_name, ext = get_fn_ext(filepath=video_path)
    if save_path is None:
        save_path = os.path.join(dir, f'{video_name}_bg_subtracted{ext}')
    else:
        check_if_dir_exists(in_dir=os.path.dirname(save_path), source=video_bg_subtraction_async.__name__)
    dt = datetime.now().strftime("%Y%m%d%H%M%S")
    temp_dir = os.path.join(os.path.dirname(save_path), f'temp_{video_name}_{dt}')
    os.makedirs(temp_dir)
    check_int(name=f'{video_bg_subtraction_async.__name__} batch_size', value=batch_size, min_value=-1)
    closing_kernel, opening_kernel = None, None
    if closing_kernel_size is not None:
        check_valid_tuple(x=closing_kernel_size, source=f'{video_bg_subtraction_async.__name__} closing_kernel_size', accepted_lengths=(2,), valid_dtypes=(int,), min_integer=1)
        check_int(name=f'{video_bg_subtraction_async.__name__} closing iterations', value=closing_iterations, min_value=1, raise_error=True)
        closing_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, closing_kernel_size)
    if opening_kernel_size is not None:
        check_valid_tuple(x=opening_kernel_size, source=f'{video_bg_subtraction_async.__name__} opening_kernel_size', accepted_lengths=(2,), valid_dtypes=(int,), min_integer=1)
        check_int(name=f'{video_bg_subtraction_async.__name__} opening iterations', value=opening_iterations, min_value=1, raise_error=True)
        opening_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, opening_kernel_size)
    if avg_frm is None:
        bg_frm = create_average_frm(video_path=bg_video_path, start_frm=bg_start_frm, end_frm=bg_end_frm, start_time=bg_start_time, end_time=bg_end_time)
    else:
        if isinstance(avg_frm, (str, os.PathLike)):
            check_file_exist_and_readable(file_path=avg_frm, raise_error=True)
            avg_frm = read_img(img_path=avg_frm, greyscale=False, clahe=False)
        check_if_valid_img(data=avg_frm, source=f'{video_bg_subtraction_async.__name__} avg_frm')
        bg_frm = np.copy(avg_frm)
    bg_frm = cv2.resize(bg_frm, (video_meta_data['width'], video_meta_data['height']))
    is_color = bg_frm.ndim == 3 and bg_frm.shape[2] == 3
    
    # Convert bg_frm to CuPy once (outside loop)
    bg_frm_cp = cp.array(bg_frm)
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*Formats.MP4_CODEC.value)
    writer = cv2.VideoWriter(save_path, fourcc, video_meta_data['fps'], (video_meta_data['width'], video_meta_data['height']), isColor=is_color)
    
    # Setup async frame reader
    async_frm_reader = AsyncVideoFrameReader(video_path=video_path, batch_size=batch_size, max_que_size=3, gpu=gpu, verbose=verbose)
    async_frm_reader.start()
    
    try:
        from simba.data_processors.cuda.image import img_stack_to_grayscale_cupy
        
        for batch_cnt in range(async_frm_reader.batch_cnt):
            start_frm, end_frm, imgs = get_async_frame_batch(batch_reader=async_frm_reader, timeout=15)
            
            if verbose:
                print(f'Processing batch {batch_cnt + 1}/{async_frm_reader.batch_cnt} (frames {start_frm}-{end_frm})...')
            
            # Convert batch to CuPy
            imgs_cp = cp.array(imgs)
            
            # Compute difference based on method
            if method == 'absolute':
                diffs = cp.abs(imgs_cp - bg_frm_cp)
            elif method == 'light':
                diffs = cp.abs(imgs_cp.astype(cp.int16) - bg_frm_cp.astype(cp.int16))
            elif method == 'dark':
                diffs = cp.abs(bg_frm_cp.astype(cp.int16) - imgs_cp.astype(cp.int16))
            else:
                diffs = cp.abs(imgs_cp - bg_frm_cp)
            
            diffs = diffs.astype(cp.uint8)
            
            # Convert to grayscale if color
            if is_color:
                gray_diff = img_stack_to_grayscale_cupy(imgs=diffs, batch_size=diffs.shape[0])
            else:
                gray_diff = diffs
            
            # Create mask
            threshold_cp = cp.array([threshold], dtype=cp.float32)
            mask = cp.where(gray_diff > threshold_cp, 1, 0).astype(cp.uint8)
            
            # Create output frames
            out_frm = imgs_cp.copy()
            
            # Apply colors
            if is_color:
                out_frm[mask == 0] = bg_color
                if fg_color is not None:
                    out_frm[mask == 1] = fg_color
            else:
                bg_clr_gray = int(0.07 * bg_color[2] + 0.72 * bg_color[1] + 0.21 * bg_color[0])
                out_frm[mask == 0] = bg_clr_gray
                if fg_color is not None:
                    fg_clr_gray = int(0.07 * fg_color[2] + 0.72 * fg_color[1] + 0.21 * fg_color[0])
                    out_frm[mask == 1] = fg_clr_gray
            
            # Convert back to numpy for morphological operations and writing
            out_frm = out_frm.astype(cp.uint8).get()
            
            # Apply morphological operations (CPU-based with OpenCV)
            for img_idx in range(out_frm.shape[0]):
                img = out_frm[img_idx]
                if opening_kernel is not None:
                    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, opening_kernel, iterations=opening_iterations)
                if closing_kernel is not None:
                    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, closing_kernel, iterations=closing_iterations)
                writer.write(img)
            
            # Free GPU memory
            del imgs_cp, diffs, gray_diff, mask, out_frm
            cp.get_default_memory_pool().free_all_blocks()
            
    finally:
        async_frm_reader.kill()
        writer.release()
    
    timer.stop_timer()
    stdout_success(msg=f'Background subtracted video saved at {save_path}', elapsed_time=timer.elapsed_time_str, source=video_bg_subtraction_async.__name__)









VIDEO_PATH = r"D:\troubleshooting\maplight_ri\project_folder\blob\videos\111.mp4"
AVG_FRM   = r"D:\troubleshooting\maplight_ri\project_folder\blob\Trial_1_C24_D1_1_bg_removed.png"
SAVE_PATH = r"D:\troubleshooting\maplight_ri\project_folder\blob\Trial_1_C24_D1_1_bg_removed.mp4"

video_bg_subtraction_async(video_path=VIDEO_PATH, avg_frm=AVG_FRM, save_path=SAVE_PATH, batch_size=100, verbose=True, gpu=True, threshold=50)
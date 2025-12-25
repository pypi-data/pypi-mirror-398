import os
import subprocess
from typing import Union
from simba.utils.checks import check_file_exist_and_readable, check_ffmpeg_available
from simba.utils.errors import FFMPEGCodecGPUError, InvalidInputError
from simba.utils.read_write import get_fn_ext, get_video_meta_data
from simba.utils.printing import SimbaTimer, stdout_success

def extract_audio_from_video(video_path: Union[str, os.PathLike],
                             save_path: Union[str, os.PathLike],
                             bitrate: str = '192k',
                             sample_rate: int = 44100) -> None:
    """
    Extract audio track from video file and save as MP3.

    :param Union[str, os.PathLike] video_path: Path to input video file.
    :param Union[str, os.PathLike] save_path: Path where the MP3 file will be saved.
    :param str bitrate: Audio bitrate (e.g., '128k', '192k', '320k'). Default: '192k'.
    :param int sample_rate: Audio sample rate in Hz. Default: 44100.
    :raises InvalidInputError: If video has no audio track or ffmpeg is not available.
    :raises FFMPEGCodecGPUError: If ffmpeg extraction fails.

    :example:
    >>> extract_audio_from_video(video_path='my_video.mp4', save_path='audio.mp3')
    >>> extract_audio_from_video(video_path='my_video.mp4', save_path='audio.mp3', bitrate='320k')
    """

    print(f'Extracting audio from {video_path}...')
    timer = SimbaTimer(start=True)
    check_file_exist_and_readable(file_path=video_path)
    check_ffmpeg_available(raise_error=True)
    
    _ = get_video_meta_data(video_path=video_path)
    
    if save_path is None:
        video_dir, video_name, _ = get_fn_ext(filepath=video_path)
        save_path = os.path.join(video_dir, f'{video_name}.mp3')
    
    save_dir = os.path.dirname(save_path)
    if save_dir and not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    if not save_path.endswith('.mp3'):
        raise InvalidInputError(msg=f'Save path must end with .mp3, got {save_path}', source='extract_audio_from_video')
    
    cmd = ['ffmpeg', '-i', str(video_path), '-vn', '-acodec', 'libmp3lame', '-ab', bitrate, '-ar', str(sample_rate), '-y', str(save_path)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise FFMPEGCodecGPUError(msg=f'Failed to extract audio from {video_path}. FFmpeg error: {result.stderr}', source='extract_audio_from_video')
    except Exception as e:
        raise FFMPEGCodecGPUError(msg=f'Error extracting audio: {str(e)}', source='extract_audio_from_video')
    
    if not os.path.isfile(save_path):
        raise FFMPEGCodecGPUError(msg=f'Audio extraction appeared to succeed but output file not found at {save_path}', source='extract_audio_from_video')
    timer.stop_timer()
    stdout_success(msg=f'Audio track saved at {save_path}', elapsed_time=timer.elapsed_time_str)


# Example usage:
extract_audio_from_video(video_path=r"E:\simba_overview_talk_202510.mp4", save_path=r"E:\simba_overview_talk_202510.mp3")


import os
import subprocess
from typing import Optional, Tuple, Union
from concurrent.futures import ProcessPoolExecutor, as_completed

from simba.utils.read_write import recursive_file_search, get_video_meta_data, get_fn_ext
from simba.utils.enums import Options
from simba.utils.printing import SimbaTimer


def _process_single_video(file_path: str,
                          overwrite: bool,
                          remove_original: bool,
                          save_dir: Optional[str]) -> str:
    """Convert a single raw H264 video into lossless MP4."""
    video_timer = SimbaTimer(start=True)
    video_meta = get_video_meta_data(video_path=file_path, fps_as_int=False)

    try:
        if save_dir:
            save_path = os.path.join(save_dir, f"{video_meta['video_name']}.mp4")
        else:
            in_dir, _, _ = get_fn_ext(filepath=file_path)
            save_path = os.path.join(in_dir, f"{video_meta['video_name']}.mp4")

        if os.path.isfile(save_path) and not overwrite:
            return f"Skipping {save_path} (already exists)"

        cmd = [
            "ffmpeg",
            "-f", "h264",
            "-framerate", str(video_meta["fps"]),
            "-i", file_path,
            "-c:v", "copy",
            "-movflags", "+faststart",
            save_path,
            "-loglevel", "error",
            "-stats",
            "-hide_banner",
            "-y",
        ]

        subprocess.run(cmd, check=True)

        if remove_original:
            os.remove(file_path)
            print(f'removed {file_path}')

        video_timer.stop_timer()
        return f"{video_meta['video_name']}: {video_timer.elapsed_time_str}s"

    except Exception as e:
        return f"Error processing {file_path}: {e}"


def lossless_mp4_conversion(directory: Union[str, os.PathLike],
                            save_dir: Optional[Union[str, os.PathLike]] = None,
                            file_extensions: Optional[Tuple[str, ...]] = None,
                            overwrite: bool = True,
                            remove_original: bool = True,
                            n_processes: Optional[int] = None):
    """
    Convert videos to lossless MP4 format using multiprocessing.
    """
    file_extensions = (
        Options.ALL_VIDEO_FORMAT_OPTIONS.value if file_extensions is None else file_extensions
    )
    file_paths = recursive_file_search(directory=directory, extensions=file_extensions, as_dict=False)

    if not file_paths:
        print("No video files found!")
        return

    print(f"Found {len(file_paths)} video(s). Starting conversion...")

    results = []
    with ProcessPoolExecutor(max_workers=n_processes) as executor:
        futures = {
            executor.submit(
                _process_single_video,
                file_path,
                overwrite,
                remove_original,
                save_dir,
            ): file_path
            for file_path in file_paths
        }

        for future in as_completed(futures):
            result = future.result()
            print(result)
            results.append(result)

    print("\n✅ Conversion complete")
    print(f"Processed {len(results)} video(s)")


if __name__ == "__main__":
    DIRECTORY = r"/mnt/data/netholabs"
    FILE_EXTENSIONS = (".h264",)
    DIRECTORY = r'C:\troubleshooting\mp_converstion_test'

    lossless_mp4_conversion(
        directory=DIRECTORY,
        file_extensions=FILE_EXTENSIONS,
        n_processes=2
    )

    # DIRECTORY = r'/mnt/data/netholabs'
    # #DIRECTORY = r'C:\troubleshooting\mp_converstion_test'
    # FILE_EXTENSIONS = ('.h264',)
    # #FILE_EXTENSIONS = ('mp4',)
    #
    # lossless_mp4_conversion(directory=DIRECTORY, file_extensions=FILE_EXTENSIONS, n_processes=7)
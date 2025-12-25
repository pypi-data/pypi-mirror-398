import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Union, Optional, Dict, List
from simba.utils.checks import check_if_dir_exists, check_valid_dataframe, check_float
from simba.utils.read_write import find_files_of_filetypes_in_directory, get_fn_ext
from simba.utils.errors import NoFilesFoundError
from simba.utils.printing import SimbaTimer, stdout_success

FRAME = 'FRAME'
CLASS_ID = 'CLASS_ID'
CONFIDENCE = 'CONFIDENCE'
CLASS_NAME = 'CLASS_NAME'
TRACK = 'TRACK'
BOX_CORD_FIELDS = ['X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4']
EXPECTED_COLS = [FRAME, CLASS_ID, CLASS_NAME, CONFIDENCE, TRACK, 'X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4']


class YoloTrackStatistics:
    """
    Compute statistics and visualize track lengths from YOLO tracking data.

    :param Union[str, os.PathLike] data_dir: Directory containing CSV files with YOLO tracking data.
    :param Optional[Union[str, os.PathLike]] save_dir: Directory where plots and results will be saved. If None, uses data_dir.
    :param int fps: Frames per second of the video. Default: 30.
    :param float min_track_length_s: Minimum track length in seconds to include in statistics. Default: 10.0.

    :example:
    >>> stats = YoloTrackStatistics(data_dir=r'E:\netholabs_videos\two_tracks_102725\tracks_cleaned', fps=30)
    >>> stats.run()
    >>> stats.plot_distribution()
    """

    def __init__(self,
                 data_dir: Union[str, os.PathLike],
                 save_dir: Optional[Union[str, os.PathLike]] = None,
                 fps: int = 30,
                 min_track_length_s: float = 10.0):

        check_if_dir_exists(in_dir=data_dir)
        check_float(name='min_track_length_s', value=min_track_length_s, min_value=0.0)
        self.data_dir = data_dir
        self.save_dir = save_dir if save_dir is not None else data_dir
        self.fps = fps
        self.min_track_length_s = min_track_length_s
        self.seconds_per_frame = 1.0 / fps  # Convert frames to seconds
        check_if_dir_exists(in_dir=self.save_dir)

        self.data_paths = find_files_of_filetypes_in_directory(
            directory=data_dir,
            extensions=('.csv',),
            as_dict=True,
            raise_error=True
        )

        if not self.data_paths:
            raise NoFilesFoundError(msg=f'No CSV files found in {data_dir}', source=self.__class__.__name__)

        self.track_lengths = {}
        self.all_track_lengths = []
        self.all_track_lengths_s = []
        self.statistics = {}

    def _compute_track_lengths(self, df: pd.DataFrame) -> Dict[int, int]:
        """
        Compute the length (number of frames) of each track in a dataframe.

        :param pd.DataFrame df: DataFrame with tracking data
        :return Dict[int, int]: Dictionary mapping track ID to track length
        """
        track_lengths = {}
        unique_tracks = df[TRACK].unique()

        for track_id in unique_tracks:
            if track_id not in [0, -1]:
                track_data = df[df[TRACK] == track_id]
                track_lengths[track_id] = len(track_data)

        return track_lengths

    def run(self) -> None:
        """
        Process all CSV files and compute track length statistics.
        """
        print(f'Computing track statistics for {len(self.data_paths)} files...')
        timer = SimbaTimer(start=True)

        for video_cnt, (video_name, data_path) in enumerate(self.data_paths.items()):
            print(f'Processing {video_name} ({video_cnt + 1}/{len(self.data_paths)})...')

            df = pd.read_csv(data_path, index_col=0)
            check_valid_dataframe(df=df, source=self.__class__.__name__, required_fields=EXPECTED_COLS)

            track_lengths = self._compute_track_lengths(df)
            
            # Convert to seconds and filter by minimum length
            track_lengths_s = {track_id: length * self.seconds_per_frame for track_id, length in track_lengths.items()}
            filtered_track_lengths = {track_id: length_frames for track_id, length_frames in track_lengths.items() 
                                     if track_lengths_s[track_id] >= self.min_track_length_s}
            filtered_track_lengths_s = [length_s for length_s in track_lengths_s.values() 
                                       if length_s >= self.min_track_length_s]
            
            self.track_lengths[video_name] = filtered_track_lengths
            self.all_track_lengths.extend(filtered_track_lengths.values())
            self.all_track_lengths_s.extend(filtered_track_lengths_s)
            
            if filtered_track_lengths_s:
                print(
                    f'  Found {len(track_lengths)} tracks ({len(filtered_track_lengths)} >= {self.min_track_length_s}s), lengths: min={min(filtered_track_lengths_s):.1f}, max={max(filtered_track_lengths_s):.1f}, mean={np.mean(filtered_track_lengths_s):.1f} (s)')
            else:
                print(f'  Found {len(track_lengths)} tracks (none >= {self.min_track_length_s}s minimum length)')
            #print(f'  Found {len(track_lengths)} tracks, lengths: min={min(track_lengths_s):.1f}, max={max(track_lengths_s):.1f}, mean={np.mean(track_lengths_s):.1f} (s)')

        self._compute_statistics()
        timer.stop_timer()
        stdout_success(msg=f'Track statistics computed for {len(self.data_paths)} files', elapsed_time=timer.elapsed_time_str)
        self._print_summary()

    def _compute_statistics(self) -> None:
        """Compute overall statistics across all tracks."""
        if not self.all_track_lengths_s:
            print('No tracks found')
            return

        self.statistics = {
            'total_tracks': len(self.all_track_lengths_s),
            'total_videos': len(self.data_paths),
            'mean_length': np.mean(self.all_track_lengths_s),
            'median_length': np.median(self.all_track_lengths_s),
            'std_length': np.std(self.all_track_lengths_s),
            'min_length': np.min(self.all_track_lengths_s),
            'max_length': np.max(self.all_track_lengths_s),
            'q25_length': np.percentile(self.all_track_lengths_s, 25),
            'q75_length': np.percentile(self.all_track_lengths_s, 75)
        }

    def _print_summary(self) -> None:
        """Print summary statistics."""
        print('\n' + '='*60)
        print('TRACK LENGTH STATISTICS SUMMARY')
        print('='*60)
        print(f'Total videos processed: {self.statistics["total_videos"]}')
        print(f'Total tracks found: {self.statistics["total_tracks"]}')
        print(f'\nTrack Length (seconds):')
        print(f'  Mean:     {self.statistics["mean_length"]:.2f} s')
        print(f'  Median:   {self.statistics["median_length"]:.2f} s')
        print(f'  Std Dev:  {self.statistics["std_length"]:.2f} s')
        print(f'  Min:      {self.statistics["min_length"]:.2f} s')
        print(f'  Max:      {self.statistics["max_length"]:.2f} s')
        print(f'  Q25:      {self.statistics["q25_length"]:.2f} s')
        print(f'  Q75:      {self.statistics["q75_length"]:.2f} s')
        print('='*60)

    def plot_distribution(self, bin_width_s: int = 5, save_plot: bool = True) -> None:
        """
        Plot histogram of track length distribution.

        :param int bin_width_s: Width of each bin in seconds. Default: 5 seconds.
        :param bool save_plot: If True, save plot to disk. Default: True.
        """
        if not self.all_track_lengths_s:
            print('No track data to plot')
            return

        print('Creating track length distribution plot...')

        # Calculate bins based on bin width
        min_length = min(self.all_track_lengths_s)
        max_length = max(self.all_track_lengths_s)
        bins = np.arange(0, max_length + bin_width_s, bin_width_s)

        fig, ax = plt.subplots(figsize=(14, 7))

        # Histogram
        ax.hist(self.all_track_lengths_s, bins=bins, edgecolor='black', alpha=0.7, color='steelblue')
        ax.axvline(self.statistics['mean_length'], color='red', linestyle='--', linewidth=2, label=f'Mean: {self.statistics["mean_length"]:.1f} s')
        ax.axvline(self.statistics['median_length'], color='orange', linestyle='--', linewidth=2, label=f'Median: {self.statistics["median_length"]:.1f} s')
        ax.set_xlabel('Track Length (seconds)', fontsize=14)
        ax.set_ylabel('Frequency', fontsize=14)
        ax.set_title(f'Track Length Distribution (n={len(self.all_track_lengths_s)} tracks, bin width={bin_width_s}s)', fontsize=16, fontweight='bold')
        ax.legend(fontsize=12, loc='upper right', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        # Set x-axis ticks to show each bin
        ax.set_xticks(bins)
        ax.tick_params(axis='x', labelsize=10)

        # Add statistics text
        stats_text = (
            f"Std: {self.statistics['std_length']:.1f} s\n"
            f"Range: [{self.statistics['min_length']:.1f}, {self.statistics['max_length']:.1f}] s"
        )
        ax.text(0.98, 0.73, stats_text, transform=ax.transAxes,
                fontsize=11, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))

        plt.tight_layout()

        if save_plot:
            save_path = os.path.join(self.save_dir, 'track_length_distribution.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f'Plot saved to {save_path}')

        plt.show()

    def save_results_to_csv(self) -> None:
        """Save track length data and statistics to CSV files."""
        # Save per-video track lengths
        rows = []
        for video_name, track_lengths in self.track_lengths.items():
            for track_id, length_frames in track_lengths.items():
                length_s = length_frames * self.seconds_per_frame
                rows.append({
                    'video': video_name,
                    'track_id': track_id,
                    'length_frames': length_frames,
                    'length_s': length_s
                })

        df = pd.DataFrame(rows)
        track_csv_path = os.path.join(self.save_dir, 'track_lengths.csv')
        df.to_csv(track_csv_path, index=False)
        print(f'Track lengths saved to {track_csv_path}')

        # Save summary statistics
        stats_df = pd.DataFrame([self.statistics])
        stats_csv_path = os.path.join(self.save_dir, 'track_statistics_summary.csv')
        stats_df.to_csv(stats_csv_path, index=False)
        print(f'Summary statistics saved to {stats_csv_path}')


stats = YoloTrackStatistics(data_dir=r'E:\netholabs_videos\primeintellect_results_simon_cleaned', save_dir=r'E:\netholabs_videos\primeintellect_results_simon_cleaned\stats', fps=30)
stats.run()
stats.plot_distribution()
stats.save_results_to_csv()


import numpy as np
import pandas as pd
from itertools import groupby, count
import os
from simba.utils.read_write import find_files_of_filetypes_in_directory, get_fn_ext
from simba.utils.checks import check_if_dir_exists, check_int
from simba.utils.printing import SimbaTimer
from simba.mixins.feature_extraction_mixin import FeatureExtractionMixin

DROP_COLS = ['NOSE_P', 'LEFT_EAR_P', 'RIGHT_EAR_P', 'LEFT_SIDE_P', 'CENTER_P', 'RIGHT_SIDE_P', 'TAIL_BASE_P', 'TAIL_MID_P', 'TAIL_END_P', 'CLASS_ID', 'CLASS_NAME', 'CONFIDENCE', 'TRACK', 'X1', 'Y1', 'X2', 'Y2', 'X3', 'Y3', 'X4', 'Y4']
USE_COLS = ['FRAME', 'NOSE_X', 'NOSE_Y', 'LEFT_EAR_X', 'LEFT_EAR_Y', 'RIGHT_EAR_X', 'RIGHT_EAR_Y', 'CENTER_X','CENTER_Y', 'TAIL_BASE_X', 'TAIL_BASE_Y']

MOVEMENT_BP = 'NOSE'

class SequifierClean:
    def __init__(self,
                 data_dir: str,
                 save_dir: str,
                 min_track_length: int,
                 max_interpolation_gap: int,
                 min_movement: int,
                 overwrite: False):

        self.data_paths = find_files_of_filetypes_in_directory(directory=data_dir, as_dict=False, extensions=['.csv'], sort_alphabetically=True, raise_error=True)
        check_int(name=f'{self.__class__.__name__} min_track_length', value=min_track_length, min_value=1)
        check_int(name=f'{self.__class__.__name__} max_interpolation_gap', value=min_track_length, min_value=0)
        check_int(name=f'{self.__class__.__name__} min_movement', value=min_movement, min_value=0)
        check_if_dir_exists(in_dir=save_dir, source=f'{self.__class__.__name__} save_dir')
        self.track_counter, self.min_track_length, self.max_interpolation_gap = 0, min_track_length, max_interpolation_gap
        self.min_movement, self.save_dir, self.overwrite = min_movement, save_dir, overwrite

    def merge_runs(self, runs, max_gap):
        if not runs:
            return []
        merged = [runs[0]]
        for s, e in runs[1:]:
            prev_s, prev_e = merged[-1]
            if s <= prev_e + 1 + max_gap:
                merged[-1] = (prev_s, max(prev_e, e))
            else:
                merged.append((s, e))

        return merged

    def run(self):
        timer = SimbaTimer(start=True)
        for file_cnt, file_path in enumerate(self.data_paths):
            video_timer = SimbaTimer(start=True)
            data = pd.read_csv(file_path, index_col=0)
            data = data.rename(columns={"CENTER_X": "TEMP_CENTER_X", "CENTER_Y": "TEMP_CENTER_Y", "CENTER_P": "TEMP_CENTER_P"})
            data = data.rename(columns={"RIGHT_SIDE_X": "CENTER_X", "RIGHT_SIDE_Y": "CENTER_Y", "RIGHT_SIDE_P": "CENTER_P"})
            data = data.rename(columns={"TEMP_CENTER_X": "RIGHT_SIDE_X","TEMP_CENTER_Y": "RIGHT_SIDE_Y","TEMP_CENTER_P": "RIGHT_SIDE_P"})
            file_name = get_fn_ext(filepath=file_path)[1]
            unique_tracks = [int(x) for x in np.unique(data['TRACK'].values) if x not in [-1, 0]]
            for track in unique_tracks:
                track_data = data[data['TRACK'] == track].drop(DROP_COLS, axis=1)
                if len(track_data) < self.min_track_length: continue
                track_frms = np.sort(track_data['FRAME'].values)
                runs = [(grp[0], grp[-1]) for _, g in groupby(track_frms, lambda i, c=count(): i - next(c)) for grp in (list(g),) if grp]
                runs = self.merge_runs(runs, self.max_interpolation_gap)
                for run in runs:
                    save_name = os.path.join(self.save_dir, f'{file_name}_track_{self.track_counter}.parquet')
                    if os.path.isfile(save_name):
                        self.track_counter += 1
                        continue
                    track_sequence = track_data[(track_data['FRAME'] >= run[0]) & (track_data['FRAME'] <= run[1])]
                    track_sequence = track_sequence[USE_COLS]
                    track_sequence = track_sequence.set_index('FRAME')
                    full_index = range(track_sequence.index.min(), track_sequence.index.max() + 1)
                    track_sequence = track_sequence.reindex(full_index, fill_value=0)
                    track_sequence = track_sequence.reset_index().rename(columns={'index': 'FRAME'})
                    track_sequence = track_sequence.mask((track_sequence <= 0) | np.isinf(track_sequence))

                    nan_cnt, df_size = track_sequence.isna().sum().sum(), track_sequence.size
                    nan_pct = round((nan_cnt/df_size)*100, 4)
                    if nan_pct > 20:
                        continue
                    for bp_name in USE_COLS:
                        try:
                            track_sequence[bp_name] = track_sequence[bp_name].interpolate(method='linear', axis=0).ffill().bfill()
                        except ValueError:
                            pass
                    if track_sequence.isna().any().any(): continue
                    track_sequence = track_sequence.drop(['FRAME'], axis=1).astype(np.int32)
                    movement_data = track_sequence[[f'{MOVEMENT_BP}_X', f'{MOVEMENT_BP}_Y']]
                    movement_data = FeatureExtractionMixin().create_shifted_df(df=movement_data).values
                    try:
                        nose_movement = np.sum(FeatureExtractionMixin().bodypart_distance(bp1_coords=movement_data[:, 0:2], bp2_coords=movement_data[:, 2:4], px_per_mm=1, in_centimeters=False))
                    except:
                        continue
                    if nose_movement < self.min_movement: continue
                    track_sequence['sequenceId'] = self.track_counter
                    track_sequence['itemPosition'] = list(range(0, len(track_sequence)))
                    if len(track_sequence) < self.min_track_length: continue
                    track_sequence.to_parquet(save_name, index=False)
                    self.track_counter += 1
            video_timer.stop_timer()
            print(f'Video {file_cnt}/{len(self.data_paths)} complete. Current track counts: {self.track_counter}')

i = SequifierClean(data_dir=r'E:\netholabs_videos\primeintellect_results_simon_cleaned',
                   save_dir=r"E:\netholabs_videos\primeintellect_results_simon_cleaned\sequifier_parquets_3",
                   min_track_length=150,
                   max_interpolation_gap=30,
                   min_movement=500,
                   overwrite=False)
i.run()
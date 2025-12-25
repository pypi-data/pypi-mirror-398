import os
from typing import Union, Optional
import numpy as np
import multiprocessing
import platform

from simba.utils.data import terminate_cpu_pool
from simba.utils.read_write import read_pickle, find_core_cnt
from simba.utils.checks import check_valid_dict, check_int, check_valid_boolean
from simba.mixins.geometry_mixin import GeometryMixin
from simba.utils.enums import Defaults, OS

class Ares2Polygons:
    """
    Converts ARES tracking data to polygon representations using parallel processing.

    :param Union[dict, str, os.PathLike] data: ARES tracking data as dictionary or path to pickle file.
    :param Optional[int] parallel_offset: Buffer distance in pixels for polygon creation. Default: 20.
    :param Optional[int] core_cnt: Number of CPU cores for multiprocessing. Use -1 for all available cores. Default: 8.
    :param bool verbose: If True, prints progress information. Default: True.

    :example:
    >>> x = Ares2Polygons(data=r'C:\projects\simba\simba\simba\sandbox\ares\ProcessedTracks.pkl', core_cnt=2)
    >>> x.run()
    """

    def __init__(self,
                 data: Union[dict, str, os.PathLike],
                 parallel_offset: Optional[int] = 20,
                 core_cnt: Optional[int] = 8,
                 verbose: bool = True):

        if isinstance(data, (str, os.PathLike)):
            self.data = read_pickle(data_path=data, verbose=False)
        else:
            check_valid_dict(x=data, valid_key_dtypes=(str,), valid_values_dtypes=(dict,))
            self.data = data
        check_int(name=f'{self.__class__.__name__} parallel_offset', value=parallel_offset, min_value=1)
        self.track_cnt, self.parallel_offset = len(self.data.keys()), parallel_offset
        check_int(name=f'{self.__class__.__name__} core_cnt', value=core_cnt, min_value=-1, unaccepted_vals=[0])
        check_int(name=f'{self.__class__.__name__} parallel_offset', value=parallel_offset, min_value=0)
        check_valid_boolean(value=verbose, source=f'{self.__class__.__name__} verbose', raise_error=True)
        self.core_cnt, self.verbose = find_core_cnt()[0] if core_cnt == -1 or core_cnt > find_core_cnt()[0] else core_cnt, verbose
        if platform.system() == OS.MAC.value: multiprocessing.set_start_method(OS.SPAWN.value, force=True)
        self.pool = multiprocessing.Pool(self.core_cnt, maxtasksperchild=Defaults.MAXIMUM_MAX_TASK_PER_CHILD.value)

    def run(self):
        self.results, cnt = {}, 0
        for track_cnt, (track_id, track_data) in enumerate(self.data.items()):
            track_points = [list(frame.values()) for frame in track_data.values()]
            max_bp_len = max([len(row) for row in track_points])
            padded = [row + [row[-1]] * (max_bp_len - len(row)) for row in track_points]
            track_arr = np.array([[[p.x, p.y] for p in row] for row in padded], dtype=np.int32)
            cnt += track_arr.shape[0]
            self.results[track_id] = GeometryMixin().multiframe_bodyparts_to_polygon(data=track_arr, parallel_offset=self.parallel_offset, core_cnt=self.core_cnt, pool=self.pool, verbose=self.verbose)
        terminate_cpu_pool(pool=self.pool)

# x = Ares2Polygons(data=r'C:\projects\simba\simba\simba\sandbox\ares\ProcessedTracks.pkl', core_cnt=2)
# x.run()
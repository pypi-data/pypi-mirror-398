from typing import Union, Optional
import os
import platform
from datetime import datetime
from itertools import combinations
import multiprocessing

from simba.sandbox.ares.ares_data_to_polygons import Ares2Polygons

from simba.mixins.geometry_mixin import GeometryMixin
from simba.utils.enums import Defaults, OS
from simba.utils.printing import SimbaTimer
from simba.utils.data import terminate_cpu_pool
from simba.utils.checks import check_file_exist_and_readable, check_if_dir_exists, check_int, check_valid_boolean
from simba.utils.read_write import get_fn_ext, read_pickle, find_core_cnt

class AresGetDistance():

    def __init__(self,
                 data_path: Union[str, os.PathLike],
                 save_path: Optional[Union[str, os.PathLike]] = None,
                 core_cnt: int = 8,
                 verbose: bool = True,
                 parallel_offset: int = 20):

        check_file_exist_and_readable(file_path=data_path, raise_error=True)
        if save_path is not None:
            check_if_dir_exists(in_dir=os.path.dirname(save_path), source=self.__class__.__name__, raise_error=True)
            self.save_path = save_path
        else:
            data_dir, data_name, _ = get_fn_ext(filepath=data_path)
            self.save_path = os.path.join(data_dir, f'{data_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}.pkl')
        self.data = read_pickle(data_path=data_path, verbose=False)
        check_int(name=f'{self.__class__.__name__} parallel_offset', value=parallel_offset, min_value=1)
        check_valid_boolean(value=verbose, source=f'{self.__class__.__name__} verbose', raise_error=True)
        if platform.system() == OS.MAC.value: multiprocessing.set_start_method(OS.SPAWN.value, force=True)
        check_int(name=f'{self.__class__.__name__} core_cnt', value=core_cnt, min_value=-1, unaccepted_vals=[0])
        self.core_cnt, self.verbose = find_core_cnt()[0] if core_cnt == -1 or core_cnt > find_core_cnt()[0] else core_cnt, verbose
        self.pool = multiprocessing.Pool(self.core_cnt, maxtasksperchild=Defaults.MAXIMUM_MAX_TASK_PER_CHILD.value)
        self.parallel_offset = parallel_offset

    def run(self):
        timer = SimbaTimer(start=True)
        print('Starting...')
        polygon_getter = Ares2Polygons(data=self.data, parallel_offset=self.parallel_offset, core_cnt=self.core_cnt)
        polygon_getter.run()
        results, cnts = {}, 0
        for cnt, (track_1, track_2) in enumerate(combinations(polygon_getter.results.keys(), r=2)):
            shapes_1, shapes_2 = polygon_getter.results[track_1], polygon_getter.results[track_2]
            results[f'{track_1}-{track_2}'] = GeometryMixin().multiframe_shape_distance(shapes_a=shapes_1, shapes_b=shapes_2, verbose=self.verbose, core_cnt=self.core_cnt, pool=self.pool)
            cnts += len(results[f'{track_1}-{track_2}'])
        timer.stop_timer()
        print('time:', timer.elapsed_time_str, cnts)
        terminate_cpu_pool(pool=self.pool)

if __name__ == "__main__":
    x = AresGetDistance(data_path=r'C:\projects\simba\simba\simba\sandbox\ares\ProcessedTracks.pkl', core_cnt=8, verbose=True, parallel_offset=20)
    x.run()
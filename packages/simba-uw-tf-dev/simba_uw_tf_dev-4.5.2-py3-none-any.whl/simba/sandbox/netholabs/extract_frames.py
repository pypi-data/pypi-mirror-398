import os
import pickle
import multiprocessing
import functools
import numpy as np
from simba.utils.read_write import read_frm_of_video
import time

def _stack_frms(time_keys, lookup, save_dir):
    start = time.time()

    batch, time_keys = time_keys
    cameras_ids = list({key for subdict in lookup.values() for key in subdict})
    results = {}
    start, end = time_keys[0], time_keys[-1]
    for camera in cameras_ids:
        results[camera] = np.full(shape=(len(time_keys), 720, 1280, 3), fill_value=0, dtype=np.uint8)

    for time_cnt, time_key in enumerate(time_keys):
        time_frms = lookup[time_key]
        print(batch, time_key)
        for camera, camera_data in time_frms.items():
            x = {k: v for k, v in camera_data.items() if v != -1}
            if len(x.keys()) > 0:
                video_path = os.path.join(list(x.keys())[0] + '_simon.mp4')
                try:
                    img = read_frm_of_video(video_path=video_path, frame_index=list(x.values())[0])
                    results[camera][time_cnt] = img
                except:
                    pass
            else:
                continue

    for k, v in results.items():

        save_path = os.path.join(save_dir, f'{k}_{start}_{end}.npz')
        print(f'Saving {save_path}')
        np.savez_compressed(save_path, arr=v)
    print(time.time() - start)


class ExtractFrames:



    def __init__(self,
                 data_dir: str,
                 save_dir: str,
                 lk: str,
                 n: int = 22):

        with open(lk, 'rb') as file:
            lookup = pickle.load(file)

        time_keys = list(lookup.keys())
        chunks = lambda lst, n: [lst[i:i + n] for i in range(0, len(lst), n)]
        time_keys = chunks(time_keys, 120)[0: 10]
        time_keys = [(i, j) for i, j in enumerate(time_keys)]

        results = {}
        with multiprocessing.Pool(32, maxtasksperchild=50) as pool:
            constants = functools.partial(_stack_frms, lookup=lookup, save_dir=save_dir)
            for batch_cnt, batch_result in enumerate(pool.imap(constants, time_keys, chunksize=1)):
                pass

                #results.update(batch_result)













        pass








if __name__ == "__main__":
    ExtractFrames(data_dir=r'D:\netholabs\temporal_stitching_2\test_temporal_stitching', lk=r"D:\netholabs\temporal_stitching_2\test_temporal_stitching\test_2.pk", save_dir=r'D:\netholabs\temporal_stitching_2\test_temporal_stitching\concat')
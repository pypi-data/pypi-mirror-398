import os
from typing import Union, Dict, Optional, Any
import numpy as np
import random
from shapely.geometry import Polygon
from simba.utils.read_write import read_sleap_csv, write_pickle, read_pickle
from simba.mixins.geometry_mixin import GeometryMixin
from simba.utils.checks import check_int
from simba.plotting.geometry_plotter import GeometryPlotter
from simba.utils.read_write import read_roi_data
from simba.utils.data import create_color_palette

def sleap_csv_to_geometries(data: Union[str, os.PathLike],
                            buffer: int = 10,
                            save_path: Optional[Union[str, os.PathLike]] = None) -> Union[None, Dict[Any, dict]]:
    """
     Convert SLEAP CSV tracking data to polygon geometries for each track and frame.

     This function reads SLEAP-exported CSV files containing pose estimation data and converts
     the body part coordinates into polygon geometries. The polygons are created by connecting
     the body parts with a specified buffer around the animal's body outline.

     :param Union[str, os.PathLike] data: Path to SLEAP CSV file containing tracking data with columns 'track', 'frame_idx', and body part coordinates.
     :param int buffer: Buffer size in pixels to add around the body part polygon. Default: 10.
     :param Optional[Union[str, os.PathLike]] save_path: Optional path to save the results as a pickle file. If None, returns the data directly.
     :return: Dictionary with track IDs as keys and frame-to-polygon mappings as values, or None if save_path is provided.
     :rtype: Union[None, Dict[Any, dict]]

     :example:
         >>> results = sleap_csv_to_geometries(data=r"C:\troubleshooting\ants\pose_data\ant.csv")
         >>> # Results structure: {track_id: {frame_idx: Polygon, ...}, ...}
     """

    TRACK, FRAME_IDX = 'track', 'frame_idx'
    check_int(name=f'{sleap_csv_to_geometries.__name__} buffer', value=buffer, min_value=1, raise_error=True)
    df, bp_names, headers = read_sleap_csv(file_path=data)
    results = {}
    track_ids = sorted(df[TRACK].unique())
    bp_cnter = max(track_ids) + 100
    for track_id in track_ids:
        track_data = df[df[TRACK] == track_id]
        track_cords = track_data[headers].fillna(-1).values.astype(np.int32).reshape(len(track_data), -1, 2)
        track_frms = track_data[FRAME_IDX].values
        polygons = GeometryMixin.bodyparts_to_polygon(data=track_cords, parallel_offset=buffer)
        # #points = GeometryMixin.multiframe_bodypart_to_point(data=track_cords, buffer=25, core_cnt=10, px_per_mm=1)
        # for bp_cnt, bp in enumerate(bp_names):
        #     x = track_data[[f'{bp}.x', f'{bp}.y']].fillna(-1).values.astype(np.int32).reshape(len(track_data), 2)
        #     points = GeometryMixin.bodyparts_to_points(data=x, buffer=25, px_per_mm=1)
        #     results[bp_cnter] = {k: None for k in range(0, df[FRAME_IDX].max() + 1)}
        #     results[bp_cnter].update({k: v for k, v in zip(track_frms, points)})
        #     bp_cnter += 1
        results[track_id] = {k: None for k in range(0, df[FRAME_IDX].max()+1)}
        results[track_id].update({k: v for k, v in zip(track_frms, polygons)})

    if save_path is not None:
        write_pickle(data=results, save_path=save_path)
    else:
        return results
#
#
def geometry_pickle_to_video(pickle_path: Union[str, os.PathLike], video_path: Union[str, os.PathLike]):
    geometry_data = read_pickle(data_path=pickle_path)
    max_frame = 0
    for track_id, track_data in geometry_data.items():
        if track_data:  # Check if track has data
            max_frame = max(max_frame, max(track_data.keys()))

    frame_geometries = []
    tracks = 0
    for track_id, track_data in geometry_data.items():
        track_data = list(track_data.values())
        frame_geometries.append(track_data)
        tracks += 1


    roi_data = read_roi_data(roi_path=r"C:\troubleshooting\ants\project_folder\logs\measures\ROI_definitions.h5")[2]['vertices'].values[0]
    p = [Polygon(roi_data)] * 33125
    frame_geometries.append(p)

    colors = create_color_palette(pallete_name='jet', increments=tracks, as_int=True)
    colors = [tuple(x) for x in colors]

    plotter = GeometryPlotter(geometries=frame_geometries, video_name=video_path,
                              save_dir=r'C:\troubleshooting\ants\pose_data',
                              colors=colors,
                              core_cnt=16,
                              shape_opacity=0.4)
    plotter.run()

#sleap_csv_to_geometries(data=r"C:\troubleshooting\ants\pose_data\ant.csv", save_path=r'C:\troubleshooting\ants\pose_data\animal_geometries.pickle', buffer=50)
#geometry_pickle_to_video(pickle_path=r"C:\troubleshooting\ants\pose_data\animal_geometries.pickle", video_path=r"C:\troubleshooting\ants\project_folder\videos\ant.mp4")


def plot_keypoints(data, video, out_path):


    df, bp_names, headers = read_sleap_csv(file_path=data)
    TRACK, FRAME_IDX = 'track', 'frame_idx'
    df, bp_names, headers = read_sleap_csv(file_path=data)
    results = {}
    track_ids = sorted(df[TRACK].unique())
    for track_id in track_ids:
        track_data = df[df[TRACK] == track_id]
        track_cords = track_data[headers].fillna(-1)
        track_frms = track_data[FRAME_IDX].values
        for bp_name in bp_names:
            bp_data =  track_cords[[f'{bp_name}.x', f'{bp_name}.y']].values.astype(np.int32).reshape(-1, 2)
            circles = GeometryMixin().bodyparts_to_circle(data=bp_data, parallel_offset=10)
            #circles = GeometryMixin().multiframe_bodyparts_to_circle(data=bp_data, parallel_offset=20, core_cnt=12)
            if len(list(results.keys())) == 0:
                point_id = 0
            else:
                point_id = max(list(results.keys())) + 1
            results[point_id] = {k: None for k in range(0, df[FRAME_IDX].max() + 1)}
            results[point_id].update({k: v for k, v in zip(track_frms, circles)})
            print(track_id, point_id)

    max_frame = 0
    for track_id, track_data in results.items():
        if track_data:  # Check if track has data
            max_frame = max(max_frame, max(track_data.keys()))

    frame_geometries = []
    tracks = 0
    for track_id, track_data in results.items():
        track_data = list(track_data.values())
        frame_geometries.append(track_data)
        tracks += 1


    clr_cnt = max(list(results.keys()))
    colors = create_color_palette(pallete_name='Paired', increments=clr_cnt, as_int=True)
    colors = [tuple(x) for x in colors]
    random.shuffle(colors)



    plotter = GeometryPlotter(geometries=frame_geometries, video_name=video,
                              save_dir=r'C:\troubleshooting\ants\pose_data\new',
                              colors=colors,
                              core_cnt=16,
                              shape_opacity=0.6)
    plotter.run()

        # print(point_id)



plot_keypoints(data=r"C:\troubleshooting\ants\pose_data\ant.csv", video=r"C:\troubleshooting\ants\pose_data\ant.mp4", out_path=r"C:\troubleshooting\ants\pose_data\ant_2.mp4")



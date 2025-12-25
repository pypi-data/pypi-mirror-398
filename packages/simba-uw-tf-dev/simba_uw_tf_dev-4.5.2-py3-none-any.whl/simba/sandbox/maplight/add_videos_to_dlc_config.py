import yaml
import copy
import os
from simba.utils.read_write import find_files_of_filetypes_in_directory, read_img

def add_videos_to_dlc_config(config_path: str):
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    video_sets = copy.copy(data['video_sets'])
    lbl_data_dir = os.path.join(os.path.dirname(config_path), 'labeled-data')
    dirs = [d for d in os.listdir(lbl_data_dir) if os.path.isdir(os.path.join(lbl_data_dir, d))]
    for dir in dirs:
        if dir in video_sets.keys():
            continue
        else:
            img_paths = find_files_of_filetypes_in_directory(directory=os.path.join(lbl_data_dir, dir), extensions=['.png'])[0]
            img = read_img(img_path=img_paths)
            h, w = img.shape[0:2]
            print(video_sets, h, w)
            video_sets[f'{dir}.mp4'] = {'crop': f'0, {w}, 0, {h}'}
            #break
    data['video_sets'] = video_sets
    with open(config_path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)

add_videos_to_dlc_config(config_path=r"E:\deeplabcut_projects\resident_intruder_white_black-SN-2025-09-30\config.yaml")
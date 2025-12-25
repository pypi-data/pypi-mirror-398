import pandas as pd
from simba.utils.read_write import recursive_file_search, copy_files_in_directory, find_files_of_filetypes_in_directory, get_fn_ext
import os
from pathlib import Path
from simba.utils.enums import Options
from PIL import Image
import shutil


#CRATE H5's deeplabcut.convertcsv2h5(r"/mnt/e/deeplabcut_projects/resident_intruder_white_black-SN-2025-09-30/config.yaml", userfeedback=False,  scorer= 'SN')

def dlc_single_to_dlc_multi(in_dir: str,
                            out_dir: str,
                            check_truncated: bool = True):

    """
    #CRATE H5's deeplabcut.convertcsv2h5(r"/mnt/e/deeplabcut_projects/resident_intruder_white_black-SN-2025-09-30/config.yaml", userfeedback=False,  scorer= 'SN')

    :param in_dir:
    :param out_dir:
    :param check_truncated:
    :return:
    """

    files = recursive_file_search(directory=in_dir, extensions=['csv'], substrings=['CollectedData_SN'])
    scorer = ["", ""] + ["SN"] * 32
    individuals = ["", ""] + [1]*16 + [2]*16
    bodyparts = ["", ""] + [
        "Ear_left","Ear_left","Ear_right","Ear_right",
        "Nose","Nose","Center","Center",
        "Lateral_left","Lateral_left","Lateral_right","Lateral_right",
        "Tail_base","Tail_base","Tail_end","Tail_end"
    ] * 2
    coords = ["", ""] + ["x","y"] * 16
    columns = pd.MultiIndex.from_arrays([scorer, individuals, bodyparts, coords], names=["scorer", "individuals", "bodyparts", "coords"])

    for file_cnt, file in enumerate(files):
        print(f'File {file_cnt+1}/{len(files)} ({file})')
        data = pd.read_csv(file)
        video_name = Path(file).parent.name
        data = data.loc[2:, ].reset_index(drop=True)
        data_split = data['scorer'].str.split(r'\\', expand=True)
        df_new = pd.concat([data_split, data], axis=1).drop(['scorer', 0], axis=1).values
        df = pd.DataFrame(columns=columns, data=df_new)
        df.index = ['labeled-data'] * len(df_new)
        save_dir = os.path.join(out_dir, video_name)
        if not os.path.isdir(save_dir): os.makedirs(save_dir)
        csv_path = os.path.join(out_dir, video_name, 'CollectedData_SN.csv')
        #
        if not check_truncated:
            copy_files_in_directory(in_dir=os.path.dirname(file), out_dir=os.path.join(out_dir, video_name), raise_error=True, filetype='png', prefix=None, verbose=True)
        else:
            img_paths = find_files_of_filetypes_in_directory(directory=os.path.dirname(file), extensions=Options.ALL_IMAGE_FORMAT_OPTIONS.value, as_dict=True)
            truncated_images, valid_imgs = [], []
            for img_name, img_path in img_paths.items():
                try:
                    with Image.open(img_path) as img:
                        img.verify()
                        valid_imgs.append(img_path)
                except (OSError, IOError):
                    truncated_images.append(img_path)
            for truncated_image in truncated_images:
                _, img_name, ext = get_fn_ext(filepath=truncated_image)
                df = df[df.iloc[:, 1] != f'{img_name}{ext}']
            for valid_img in valid_imgs:
                _, img_name, ext = get_fn_ext(filepath=valid_img)
                dest = os.path.join(save_dir, f'{img_name}{ext}')
                shutil.copy(valid_img, dest)
        df.to_csv(csv_path)


x = dlc_single_to_dlc_multi(in_dir=r'E:\dlc_pose_annotations', out_dir=r'E:\dlc_pose_reformat')
from typing import Union
import os
import json
from simba.utils.checks import check_if_keys_exist_in_dict, check_valid_boolean, check_if_dir_exists
from simba.utils.read_write import create_directory, get_fn_ext
import cv2
from simba.utils.read_write import find_files_of_filetypes_in_directory
from simba.third_party_label_appenders.converters import b64_to_arr, split_yolo_train_test_val
from simba.utils.printing import SimbaTimer, stdout_success

def labelme_to_yolo(labelme_dir: Union[str, os.PathLike],
                    save_dir: Union[str, os.PathLike],
                    obb: bool = False,
                    verbose: bool = True) -> None:
    """
    Convert LabelMe annotations in json to YOLO format and save the corresponding images and labels in txt format.

    .. note::
       For more information on the LabelMe annotation tool, see the `LabelMe GitHub repository <https://github.com/wkentaro/labelme>`_.

    :param Union[str, os.PathLike labelme_dir: Path to the directory containing LabelMe annotation `.json` files.
    :param Union[str, os.PathLike save_dir: Directory where the YOLO-format images and labels will be saved. Will create 'images/', 'labels/', and 'map.json' inside this directory.
    :param bool obb: If True, saves annotations as oriented bounding boxes (8 coordinates). If False, uses standard YOLO format (x_center, y_center, width, height)
    :param bool verbose: If True, prints progress messages during conversion.


    :example:
    >>> LABELME_DIR = r'D:/annotations'
    >>> SAVE_DIR = r"D:/yolo_data"
    >>> labelme_to_yolo(labelme_dir=LABELME_DIR, save_dir=SAVE_DIR)
    """

    timer = SimbaTimer(start=True)
    check_if_dir_exists(in_dir=os.path.dirname(save_dir), source=f'{labelme_to_yolo.__name__} save_dir', raise_error=True)
    check_if_dir_exists(in_dir=labelme_dir, source=f'{labelme_to_yolo.__name__} labelme_dir', raise_error=True)
    labelme_file_paths = find_files_of_filetypes_in_directory(directory=labelme_dir, extensions=['.json'], raise_error=True)
    save_img_dir = os.path.join(save_dir, 'images')
    save_labels_dir = os.path.join(save_dir, 'labels')
    map_path = os.path.join(save_dir, 'map.json')
    create_directory(paths=save_img_dir, overwrite=True)
    create_directory(paths=save_labels_dir, overwrite=True)
    check_valid_boolean(value=[verbose], source=f'{labelme_to_yolo.__name__} verbose', raise_error=True)
    check_valid_boolean(value=[obb], source=f'{labelme_to_yolo.__name__} obb', raise_error=True)
    labels = {}
    for file_cnt, file_path in enumerate(labelme_file_paths):
        if verbose: print(f'Labelme to YOLO file {file_cnt+1}/{len(labelme_file_paths)}...')
        with open(file_path) as f: annot_data = json.load(f)
        check_if_keys_exist_in_dict(data=annot_data, key=['shapes', 'imageData', 'imagePath'], name=file_path)
        img_name = get_fn_ext(filepath=annot_data['imagePath'])[1]
        img = b64_to_arr(annot_data['imageData'])
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_h, img_w = img.shape[:2]
        label_save_path = os.path.join(save_labels_dir, f'{img_name}.txt')
        img_save_path = os.path.join(save_img_dir, f'{img_name}.png')
        roi_str = ''
        for bp_data in annot_data['shapes']:
            check_if_keys_exist_in_dict(data=bp_data, key=['label', 'points', 'shape_type'], name=file_path)
            if bp_data['shape_type'] == 'rectangle':
                if bp_data['label'] not in labels.keys():
                    label_id = len(labels.keys())
                    labels[bp_data['label']] = len(labels.keys())
                else:
                    label_id = labels[bp_data['label']]
                x1, y1 = bp_data['points'][0]
                x2, y2 = bp_data['points'][1]
                x_min, x_max = sorted([x1, x2])
                y_min, y_max = sorted([y1, y2])
                if not obb:
                    w = (x_max - x_min) / img_w
                    h = (y_max - y_min) / img_h
                    x_center = (x_min + (x_max - x_min) / 2) / img_w
                    y_center = (y_min + (y_max - y_min) / 2) / img_h
                    roi_str += ' '.join([f"{label_id}", str(x_center), str(y_center), str(w), str(h) + '\n'])
                else:
                    top_left = (x_min / img_w, y_min / img_h)
                    top_right = (x_max / img_w, y_min / img_h)
                    bottom_right = (x_max / img_w, y_max / img_h)
                    bottom_left = (x_min / img_w, y_max / img_h)
                    roi_str += ' '.join([f"{label_id}", str(top_left[0]), str(top_left[1]), str(top_right[0]), str(top_right[1]), str(bottom_right[0]), str(bottom_right[1]), str(bottom_left[0]), str(bottom_left[1]) + '\n'])
        with open(label_save_path, mode='wt', encoding='utf-8') as f:
            f.write(roi_str)
        cv2.imwrite(img_save_path, img)
    with open(map_path, 'w') as f:
        json.dump(labels, f, indent=4)
        print(labels)
    timer.stop_timer()
    if verbose: stdout_success(msg=f'Labelme to YOLO conversion complete. Data saved in directory {save_dir}.', elapsed_time=timer.elapsed_time_str)



# split_yolo_train_test_val(data_dir=r'D:\netholabs\yolo_test\yolo_data', save_dir=r"D:\netholabs\yolo_test\yolo_train", verbose=True)

#


# LABELME_DIR = r'D:\netholabs\yolo_test\annotations'
# SAVE_DIR = r"D:\netholabs\yolo_test\yolo_data"
# labelme_to_yolo(labelme_dir=LABELME_DIR, save_dir=SAVE_DIR)
import os
from PIL import Image, ImageFile
from simba.utils.read_write import find_files_of_filetypes_in_directory
ImageFile.LOAD_TRUNCATED_IMAGES = False  # we want to detect truncation
import pandas as pd
#
#
#
# def delete_trunacted_annotations(config_path: str):
#
#     img_folder = os.path.join(os.path.dirname(config_path), 'labeled-data')
#     dirs = [d for d in os.listdir(img_folder) if os.path.isdir(os.path.join(img_folder, d))]
#     for dir in dirs:
#         video_dir = os.path.join(img_folder, dir)
#         data_path = os.path.join(video_dir, 'CollectedData_SN.csv')
#         img_paths = find_files_of_filetypes_in_directory(directory=video_dir, extensions=['.png'])
#         truncated_video_imgs = []
#         for img_path in img_paths:
#             try:
#                 with Image.open(img_path) as img:
#                     img.verify()  # verify checks for truncation or corruption
#             except (OSError, IOError):
#                 truncated_video_imgs.append(img_path)
#         if len(truncated_video_imgs) > 0:
#             data = pd.read_csv(data_path)
#             print(data)
#             break
#
#     pass
#
#





image_folder = r"E:\deeplabcut_projects\resident_intruder_white_black-SN-2025-09-30\labeled-data"  # change this to your folder
truncated_images = []

for root, _, files in os.walk(image_folder):
    for file in files:
        if file.lower().endswith((".png", ".jpg", ".jpeg")):
            path = os.path.join(root, file)
            try:
                with Image.open(path) as img:
                    img.verify()  # verify checks for truncation or corruption
            except (OSError, IOError):
                truncated_images.append(path)

print(f"Found {len(truncated_images)} truncated/corrupt images:")
for img_path in truncated_images:
    print(img_path)



#delete_trunacted_annotations(config_path=r"E:\deeplabcut_projects\resident_intruder_white_black-SN-2025-09-30\config.yaml")
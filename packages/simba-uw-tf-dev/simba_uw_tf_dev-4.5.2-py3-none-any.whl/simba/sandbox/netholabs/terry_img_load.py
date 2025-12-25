import os
import h5py
import numpy as np
import imageio


mat_path = r"E:\netholabs_videos\terry\mp4s\4_02_001_exp_2025_12_02_17_50_00\labeling\frameCache_f75.mat"
out_dir = r"E:\netholabs_videos\terry\mp4s\4_02_001_exp_2025_12_02_17_50_00\labeling\imgs"

os.makedirs(out_dir, exist_ok=True)

with h5py.File(mat_path, "r") as f:
    vids = f["videos"][()]   # (1, 6) object references

    for cam in range(vids.shape[1]):
        print(f"Extracting camera {cam}...")

        # dereference dataset for this camera
        cam_data = f[vids[0, cam]][()]   # (75, 3, 2028, 1520)

        # convert (75, 3, H, W) → (75, H, W, 3)
        cam_data = np.moveaxis(cam_data, 1, -1)
        print(cam_data)

        # output folder for this camera
        cam_dir = os.path.join(out_dir, f"cam{cam}")
        os.makedirs(cam_dir, exist_ok=True)

        # save frames
        for i in range(cam_data.shape[0]):
            print(i)
            img_path = os.path.join(cam_dir, f"frame_{i:03d}.png")
            imageio.imwrite(img_path, cam_data[i])
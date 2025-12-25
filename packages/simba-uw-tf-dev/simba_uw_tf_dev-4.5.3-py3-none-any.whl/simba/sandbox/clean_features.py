import os.path

import pandas as pd
from simba.utils.read_write import recursive_file_search


def clean_features(data_dir, save_dir):
    file_paths = recursive_file_search(directory=data_dir, extensions='csv', as_dict=True)

    for video_name, file_path in file_paths.items():
        data = pd.read_csv(file_path, index_col=0).reset_index(drop=True)
        cols_bps = list(data.columns[0:48])
        cols_bps.append(data.columns[-1])
        out_data = data[cols_bps]
        save_directory = os.path.join(save_dir, data.columns[-1])
        if not os.path.isdir(save_directory):
            os.makedirs(save_directory)
        save_path = os.path.join(save_directory, f'{video_name}.csv')
        out_data.to_csv(save_path)
        print(save_path)
        #break



    pass





clean_features(data_dir=r'E:\annotations_preprint\Annotations', save_dir=r'E:\features_removed')



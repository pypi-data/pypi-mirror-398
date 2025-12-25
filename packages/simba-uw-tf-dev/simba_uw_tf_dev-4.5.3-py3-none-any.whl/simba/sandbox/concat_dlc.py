from typing import Union
import os
import pandas as pd
from pathlib import Path

from simba.utils.checks import check_if_dir_exists
from simba.utils.read_write import recursive_file_search, create_directory, copy_files_in_directory
from simba.utils.enums import Formats

def concatenate_dlc_annotations(data_dir: Union[str, os.PathLike], save_dir: Union[str, os.PathLike], annotator: str = 'SN'):
    """
    Concatenate DeepLabCut annotation files from multiple directories into a single CSV file.

    This function searches for DeepLabCut 'CollectedData_*.csv' files in the specified data directory,
    processes each file to standardize frame naming conventions, copies associated PNG images,
    and combines all annotation data into a single CSV file with multi-index headers.

    :param Union[str, os.PathLike] data_dir: Path to directory containing DeepLabCut annotation subdirectories.
    :param Union[str, os.PathLike] save_dir: Path to directory where concatenated results will be saved.
    :param str annotator: Name of the annotator (default: 'SN'). Used in the output filename 'CollectedData_{annotator}.csv'.

    :return: None. Creates concatenated CSV file and copies PNG images to 'labeled-data' subdirectory in save_dir.

    :example:
    >>> concatenate_dlc_annotations(
    ...     data_dir='/path/to/dlc/annotations',
    ...     save_dir='/path/to/output',
    ...     annotator='John'
    ... )
    """

    check_if_dir_exists(in_dir=data_dir, source=concatenate_dlc_annotations.__name__, raise_error=True)
    check_if_dir_exists(in_dir=save_dir, source=concatenate_dlc_annotations.__name__, raise_error=True)
    out_dir = os.path.join(f'{save_dir}', 'labeled-data')
    df_destination = os.path.join(out_dir, f'CollectedData_{annotator}.csv')
    create_directory(out_dir)

    df_results = []
    annotation_paths = recursive_file_search(directory=data_dir, extensions=Formats.CSV.value, case_sensitive=True, substrings='CollectedData', raise_error=True, as_dict=False)
    for file_cnt, annotation_path in enumerate(annotation_paths):
        df = pd.read_csv(annotation_path, header=[0, 1, 2])
        video_name = Path(annotation_path).parent.name
        df.iloc[:, 0] = df.iloc[:, 0].str.rsplit("\\", n=1).str.join("_")
        copy_files_in_directory(in_dir=os.path.dirname(annotation_path), out_dir=out_dir, raise_error=True, filetype='png', prefix=f'{video_name}_', verbose=True)
        df_results.append(df)
        print(f'File {file_cnt+1}/{len(annotation_paths)} complete...')
    df_results = pd.concat(df_results, axis=0)
    df_results.to_csv(df_destination, index=False)








#concatenate_dlc_annotations(data_dir=r'E:\rgb_white_vs_black_imgs', save_dir=r'E:\rgb_white_vs_black_imgs\concat')



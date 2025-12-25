from typing import Union, List
import os
from copy import deepcopy
from simba.utils.checks import check_if_dir_exists, check_valid_lst, check_valid_dataframe, check_if_df_field_is_boolean
from simba.utils.read_write import find_files_of_filetypes_in_directory, read_df, get_fn_ext, write_df
from simba.utils.errors import NoDataError
from simba.utils.enums import Formats

def append_targets(features_dir: Union[str, os.PathLike],
                   targets_dir: Union[str, os.PathLike],
                   save_dir: Union[str, os.PathLike],
                   target_names: List[str]):

    """
    Append target columns from target CSV files to corresponding feature CSV files.

    This function reads feature files from one directory and target files from another directory,
    then appends the specified target columns to the feature data and saves the combined results
    to a third directory. The function ensures that target files exist for each feature file
    and validates that target columns contain boolean data.

    :param Union[str, os.PathLike] features_dir: Path to directory containing feature CSV files.
    :param Union[str, os.PathLike] targets_dir: Path to directory containing target CSV files.
    :param Union[str, os.PathLike] save_dir: Path to directory where combined files will be saved.
    :param List[str] target_names: List of target column names to append from target files.
    :raises NoDataError: If feature files are missing corresponding target files.
    :raises InvalidInputError: If target columns are not boolean or data validation fails.


    :example:
    >>> append_targets(features_dir='/path/to/features',targets_dir='/path/to/targets', save_dir='/path/to/output',target_names=['behavior_1', 'behavior_2'])
    """

    check_if_dir_exists(in_dir=features_dir, source=append_targets.__name__, raise_error=True)
    check_if_dir_exists(in_dir=targets_dir, source=append_targets.__name__, raise_error=True)
    check_if_dir_exists(in_dir=save_dir, source=append_targets.__name__, raise_error=True)
    check_valid_lst(data=target_names, source=append_targets.__name__, raise_error=True, valid_dtypes=(str,))
    features_paths = find_files_of_filetypes_in_directory(directory=features_dir, extensions=['.csv'], as_dict=True, raise_error=True)
    targets_paths = find_files_of_filetypes_in_directory(directory=targets_dir, extensions=['.csv'], as_dict=True, raise_error=True)

    missing_targets = [x for x in targets_paths.keys() if x not in features_paths]
    if len(missing_targets) > 0:
        raise NoDataError(msg=f'{len(missing_targets)} feature files are missing target files: {missing_targets}', source=append_targets.__name__)

    for file_name, file_path in features_paths.items():
        features_df = read_df(file_path, file_type='csv')
        targets_df = read_df(targets_paths[file_name], file_type='csv')
        _, video_name, _ = get_fn_ext(filepath=file_path)
        print(video_name)
        save_path = os.path.join(save_dir, f'{video_name}.csv')
        results = deepcopy(features_df)
        check_valid_dataframe(df=features_df, source=file_path, valid_dtypes=Formats.NUMERIC_DTYPES.value)
        check_valid_dataframe(df=targets_df, source=targets_paths[file_name], valid_dtypes=Formats.NUMERIC_DTYPES.value, required_fields=target_names)
        for target_name in target_names:
            check_if_df_field_is_boolean(df=targets_df, field=target_name, df_name=targets_paths[file_name])
            results[target_name] = targets_df[target_name]
        write_df(df=results, file_type='csv', save_path=save_path)



#
target_names = ['supported rearing', 'unsupported rearing']


append_targets(features_dir=r"C:\troubleshooting\open_field_rearing\project_folder\csv\features_extracted",
               targets_dir=r'C:\troubleshooting\open_field_rearing\project_folder\csv\targets_inserted',
               save_dir=r'C:\troubleshooting\open_field_rearing\project_folder\csv\targets_inserted\new_targets',
               target_names=target_names)


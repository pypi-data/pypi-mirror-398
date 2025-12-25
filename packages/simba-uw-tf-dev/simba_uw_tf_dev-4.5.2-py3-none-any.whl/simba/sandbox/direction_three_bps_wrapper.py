import time
from typing import List, Optional
import numpy as np
import pandas as pd

from simba.utils.enums import Formats
from simba.utils.checks import check_valid_array, check_valid_dataframe, check_float, check_valid_boolean
from simba.mixins.circular_statistics import CircularStatisticsMixin
from simba.mixins.train_model_mixin import TrainModelMixin
from numba import njit, typed
from simba.utils.read_write import find_files_of_filetypes_in_directory, read_df
from simba.mixins.feature_extraction_mixin import FeatureExtractionMixin


def keypoint_distances(a: np.ndarray, b: np.ndarray, px_per_mm: Optional[float] = 1, in_centimeters: Optional[bool] = False) -> np.ndarray:

    """
    Compute Euclidean distances between corresponding 2D keypoints with unit conversion.

    Given two arrays of 2D coordinates (x, y) sampled across frames, this function computes the
    frame-wise Euclidean distance between matching rows, converts from pixels to millimeters
    using ``px_per_mm``, and optionally reports distances in centimeters. Input validity is checked
    and the output is guaranteed to be ``np.float32``.

    .. seealso::
       For numba decorated function, :func:`simba.mixins.feature_extraction_mixin.FeatureExtractionMixin.framewise_euclidean_distance`
       For GPU CuPy solution, see :func:`simba.data_processors.cuda.statistics.get_euclidean_distance_cupy`.
       For GPU numba CUDA solution, see :func:`simba.data_processors.cuda.statistics.get_euclidean_distance_cuda`.

    .. image:: _static/img/framewise_euclid_dist.webp
       :width: 300
       :align: center

    .. csv-table::
       :header: EXPECTED RUNTIMES
       :file: ../../docs/tables/keypoint_distances.csv
       :widths: 20, 20, 20, 20, 20
       :align: center
       :header-rows: 1

    :param np.ndarray a: Array of shape ``(n_frames, 2)`` with non-negative numeric [x, y] coordinates.
    :param np.ndarray b: Array of shape ``(n_frames, 2)`` with non-negative numeric [x, y] coordinates. Must have the same number of rows as ``a``.
    :param float px_per_mm: Pixels-per-millimeter scaling factor (> 0). Distances are divided by this value.
    :param bool in_centimeters: If ``True``, returned distances are reported in centimeters (mm/10).
    :return: Frame-wise distances between corresponding rows in ``a`` and ``b`` (mm or cm).
    :rtype: np.ndarray

    :example:
    >>> a = np.array([[0, 0], [3, 4], [6, 8]], dtype=np.float32)
    >>> b = np.array([[0, 0], [0, 0], [3, 4]], dtype=np.float32)
    >>> # px_per_mm = 1 -> distances reported in millimeters (same numeric scale as pixels)
    >>> d_mm = keypoint_distances(a=a, b=b, px_per_mm=1.0, in_centimeters=False)
    >>> d_cm = keypoint_distances(a=a, b=b, px_per_mm=1.0, in_centimeters=True)
    """

    check_valid_array(data=a, source=f'{keypoint_distances.__name__} a', accepted_ndims=(2,), accepted_axis_1_shape=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0)
    check_valid_array(data=b, source=f'{keypoint_distances.__name__} b', accepted_ndims=(2,), accepted_axis_1_shape=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0, accepted_axis_0_shape=(a.shape[0],))
    check_float(name=f'{keypoint_distances.__name__} px_per_mm', value=px_per_mm, allow_zero=False, min_value=10e-16, raise_error=True)
    check_valid_boolean(value=in_centimeters, source=f'{keypoint_distances.__name__} in_centimeters', raise_error=True)

    d = np.linalg.norm(a - b, axis=1) / px_per_mm
    if in_centimeters:
        d = d / 10.0
    return d.astype(np.float32, copy=False)

sizes = [100, 1_000_000, 10_000_000, 20_000_000, 40_000_000, 80_000_000, 160_000_000]
for size in sizes:
    times_numba = []
    times_numpy = []
    for i in range(3):
        a = np.random.randint(0, 5, (size, 2))
        b = np.random.randint(0, 5, (size, 2))
        start = time.time()
        p = FeatureExtractionMixin.bodypart_distance(bp1_coords=a, bp2_coords=b)
        times_numba.append(time.time() -start)
        start = time.time()
        keypoint_distances(a=a, b=b)
        times_numpy.append(time.time() - start)

    print(size, '\t', np.mean(times_numba), np.std(times_numba))
    print(size, '\t', np.mean(times_numpy), np.std(times_numpy))



# def three_point_direction(nose_loc: np.ndarray,
#                           left_ear_loc: np.ndarray,
#                           right_ear_loc: np.ndarray)  -> np.ndarray:
#     """
#     Calculate animal heading direction using three anatomical landmarks with input validation.
#
#     Computes the mean directional angle of an animal based on nose and ear coordinates
#     using circular statistics. Provides a robust estimate of the animal's facing direction by calculating individual directional vectors from each ear to the nose, then computing their
#     circular mean to handle angular discontinuities properly.
#
#     The function serves as a validated wrapper around the underlying numba-accelerated implementation, ensuring input data meets requirements before computation.
#
#     .. seealso::
#        For the underlying numba-accelerated implementation, see :func:`simba.mixins.circular_statistics.CircularStatisticsMixin.direction_three_bps`.
#        For two-point direction calculation, see :func:`simba.mixins.circular_statistics.CircularStatisticsMixin.direction_two_bps`.
#
#     .. image:: _static/img/angle_from_3_bps.png
#        :width: 600
#        :align: center
#
#     .. csv-table::
#        :header: EXPECTED RUNTIMES
#        :file: ../../../docs/tables/three_point_direction.csv
#        :widths: 10, 45, 45
#        :align: center
#        :header-rows: 1
#
#     :param np.ndarray nose_loc: 2D array with shape (n_frames, 2) containing [x, y] pixel coordinates  of the nose for each frame. Must contain non-negative numeric values.
#     :param np.ndarray left_ear_loc: 2D array with shape (n_frames, 2) containing [x, y] pixel coordinates  of the left ear for each frame. Must have the same number of frames as nose_loc.
#     :param np.ndarray right_ear_loc: 2D array with shape (n_frames, 2) containing [x, y] pixel coordinates of the right ear for each frame. Must have the same number of frames as nose_loc.
#     :return: 1D array with shape (n_frames,) containing directional angles in degrees [0, 360)  for each frame. Contains NaN values for frames where computation fails.
#     :rtype: np.ndarray
#
#     :example:
#     >>> nose_loc = np.array([[100, 150], [102, 148], [105, 145]], dtype=np.float32)
#     >>> left_ear_loc = np.array([[95, 160], [97, 158], [100, 155]], dtype=np.float32)
#     >>> right_ear_loc = np.array([[105, 160], [107, 158], [110, 155]], dtype=np.float32)
#     >>> directions = CircularStatisticsMixin.direction_three_bps( nose_loc=nose_loc, left_ear_loc=left_ear_loc, right_ear_loc=right_ear_loc)
#     """
#
#     check_valid_array(data=nose_loc, source=f'{three_point_direction.__name__} nose_loc', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True)
#     check_valid_array(data=left_ear_loc, source=f'{three_point_direction.__name__} left_ear_loc', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True, accepted_axis_0_shape=(nose_loc.shape[0],))
#     check_valid_array(data=right_ear_loc, source=f'{three_point_direction.__name__} right_ear_loc', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True, accepted_axis_0_shape=(right_ear_loc.shape[0],))
#
#     results = CircularStatisticsMixin().direction_three_bps(nose_loc=nose_loc.astype(np.float32),
#                                                             left_ear_loc=left_ear_loc.astype(np.float32),
#                                                             right_ear_loc=right_ear_loc.astype(np.float32))
#     return results
#
#


# def two_point_direction(anterior_loc: np.ndarray, posterior_loc: np.ndarray)  -> np.ndarray:
#
#     """
#     Calculate directional angles between two body parts.
#
#     Computes frame-wise directional angles from posterior to anterior body parts (e.g., tail to nose, nape to head) using arctangent calculations.
#
#     It is a validated wrapper around the optimized numba implementation.
#
#     .. seealso::
#        For the underlying numba-accelerated implementation, see :func:`simba.mixins.circular_statistics.CircularStatisticsMixin.direction_two_bps`
#        For three-point direction calculation, see :func:`simba.mixins.circular_statistics.CircularStatisticsMixin.three_point_direction` or :func:`simba.mixins.circular_statistics.CircularStatisticsMixin.direction_three_bps`
#
#     .. csv-table::
#        :header: EXPECTED RUNTIMES
#        :file: ../../../docs/tables/two_point_direction.csv
#        :widths: 10, 45, 45
#        :align: center
#        :header-rows: 1
#
#     :param np.ndarray anterior_loc: 2D array with shape (n_frames, 2) containing [x, y] coordinates for the anterior body part (e.g., nose, head). Must contain non-negative numeric values.
#     :param np.ndarray posterior_loc : np.ndarray 2D array with shape (n_frames, 2) containing [x, y] coordinates for the posterior body part (e.g., tail base, nape). Must contain non-negative numeric values.
#     :return: 1D array with shape (n_frames,) containing directional angles in degrees [0, 360)  for each frame at type float32. Contains NaN values for frames where computation fails.
#     :rtype: np.ndarray
#     """
#
#     check_valid_array(data=anterior_loc, source=f'{two_point_direction.__name__} anterior_loc', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True, accepted_axis_1_shape=[2,])
#     check_valid_array(data=posterior_loc, source=f'{two_point_direction.__name__} posterior_loc', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True, accepted_axis_0_shape=(anterior_loc.shape[0],), accepted_axis_1_shape=[2,])
#     results = CircularStatisticsMixin().direction_two_bps(anterior_loc=anterior_loc.astype(np.float32), posterior_loc=posterior_loc.astype(np.float32))
#
#     return results

# def angle_to_cardinal(data: np.ndarray) -> List[str]:
#     """
#     Convert degree angles to cardinal direction bucket e.g., 0 -> "N", 180 -> "S"
#
#     .. note::
#        To convert cardinal literals to integers, map using :func:`simba.utils.enums.lookups.cardinality_to_integer_lookup`.
#        To convert integers to cardinal literals, map using :func:`simba.utils.enums.lookups.integer_to_cardinality_lookup`.
#
#     .. image:: _static/img/degrees_to_cardinal.png
#        :width: 600
#        :align: center
#
#     .. seealso::
#        For numba function, see func:`simba.mixins.circular_statistics.CircularStatisticsMixin.degrees_to_cardinal`
#        Appears to be quicker in pure numpy.
#
#     .. csv-table::
#        :header: EXPECTED RUNTIMES
#        :file: ../../../docs/tables/angle_to_cardinal.csv
#        :widths: 10, 45, 45
#        :align: center
#        :header-rows: 1
#
#     :param np.ndarray data: 1D array of degrees in range [0, 360).
#     :return: List of strings representing frame-wise cardinality.
#     :rtype: List[str]
#
#     :example:
#     >>> data = np.array(list(range(0, 405, 45))).astype(np.float32)
#     >>> CircularStatisticsMixin().angle_to_cardinal(data=data)
#     ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']
#     """
#
#     check_valid_array(data=data, source=f'{angle_to_cardinal.__name__} angle_to_cardinal', accepted_ndims=(1,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, max_value=360, raise_error=True)
#     DIRECTIONS = np.array(["N", "NE", "E", "SE", "S", "SW", "W", "NW"], dtype='<U2')
#     indices = np.round(data / 45.0).astype(int) % 8
#     return DIRECTIONS[indices].tolist()


#
# def find_collinear_features(data: pd.DataFrame,
#                             threshold: float) -> List[str]:
#
#     """
#     Identify collinear features in a pandas DataFrame for removal.
#
#     Finds pairs of features with Pearson correlation coefficients above the specified threshold and returns the names of features that should be removed to reduce multicollinearity.
#
#     Serves as a validation wrapper around numba implementation.
#
#     .. seealso::
#        For the underlying numba-accelerated implementation, see :func:`simba.mixins.train_model_mixin.TrainModelMixin.find_highly_correlated_fields`
#        For non-numba statistical methods, see :func:`simba.mixins.statistics_mixin.Statistics.find_collinear_features`
#
#     :param pd.DataFrame data: Input DataFrame containing numeric features. Each column represents a feature and each row represents an observation. Must contain only numeric data types.
#     :param float threshold: Correlation threshold for identifying collinear features. Must be between 0.0 and 1.0. Higher values (e.g., 0.9) identify only very highly correlated features, while lower values  (e.g., 0.1) identify more loosely correlated features.
#     :return: List of column names that are highly correlated with other features and should be considered for removal to reduce multicollinearity.
#     :rtype: List[str]
#
#     :example:
#     >>> a = np.random.randint(0, 5, (1_000_000, size))
#     >>> df = pd.DataFrame(a)
#     >>> c = find_collinear_features(data=df, threshold=0.0025)
#     """
#
#
#     check_valid_dataframe(df=data, source=f'{find_collinear_features.__name__} data', valid_dtypes=Formats.NUMERIC_DTYPES.value, allow_duplicate_col_names=False)
#     check_float(name=f'{find_collinear_features.__name__} threshold', value=threshold, min_value=0, max_value=1, raise_error=True)
#
#     field_names = typed.List([str(x) for x in data.columns])
#
#     x = TrainModelMixin.find_highly_correlated_fields(data=data.values.astype(np.float32),
#                                                       threshold=np.float64(threshold),
#                                                       field_names=field_names)
#     return list(x)
#
#



    #     df = pd.DataFrame(a)
    #     start = time.time()
    #     c = find_collinear_features(data=df, threshold=0.0025)
    #     times.append(time.time() - start)
    # print(size, '\t', np.mean(times), np.std(times))

# DATA_PATH = r"C:\troubleshooting\jax_examples\data"
# data_files = find_files_of_filetypes_in_directory(directory=DATA_PATH, extensions=['.csv'], as_dict=True)
# data = []
# for cnt, (video_name, video_path) in enumerate(data_files.items()):
#   print(f'Reading file {cnt+1} / {len(data_files.keys())}...')
#   df = read_df(file_path=video_path, file_type='csv')
#   data.append(df)
#
# data = pd.concat(data, axis=0)
# s = find_collinear_features(data=data, threshold=0.01)
#


#sizes = [100] #, 1_000_000, 10_000_000, 20_000_000, 40_000_000, 80_000_000, 160_000_000]
#
# for size in sizes:
#     times = []
#     for i in range(1):
#         a = np.random.randint(0, 360, (size,))
# #         start = time.time()
# #         x = find_collinear_features(data=a)
# #         times.append(time.time() -start)
# #     print(size, '\t', np.mean(times), np.std(times))
# #

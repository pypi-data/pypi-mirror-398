import time

import numpy as np
from simba.mixins.feature_extraction_mixin import FeatureExtractionMixin
from simba.utils.checks import check_valid_array, check_float, check_valid_boolean, check_str
from simba.utils.enums import Formats
from simba.feature_extractors.perimeter_jit import jitted_hull, get_hull_sizes


file_sizes = [10000, 1_000_000, 5_000_000, 10_000_000, 20_000_000]
for i in file_sizes:
    times = []
    for j in range(3):
        points = np.random.randint(0, 500, size=(i, 7, 2))
        start = time.time()
        x = get_hull_sizes(points=points)
        times.append(time.time() - start)
    print(i, np.mean(times), np.std(times))
# file_sizes = [10000, 1_000_000, 5_000_000, 10_000_000, 20_000_000, 40_000_000, 80_000_000, 120_000_000]
# for i in file_sizes:
#     times = []
#     for j in range(3):
#         bp1_coords = np.random.randint(0, 500, size=(i, 2))
#         bp2_coords = np.random.randint(0, 500, size=(i, 2))
#         start = time.time()
#         x = FeatureExtractionMixin().bodypart_distance(bp1_coords=bp1_coords, bp2_coords=bp2_coords, px_per_mm=1.0, in_centimeters=False)
#         times.append(time.time() - start)
#     print(i, np.mean(times), np.std(times))

# def get_hull_sizes(points: np.ndarray,
#                    target: str = "perimeter"):
#
#     """
#     Calculate convex hull geometric properties (perimeter or area) for sets of 2D points across multiple frames.
#
#     This function computes convex hull attributes for body part coordinates across video frames, providing
#     a measure of the overall spatial extent and shape of tracked points. The convex hull represents the
#     smallest convex polygon that contains all input points for each frame.
#
#     .. seealso::
#        Wrapper function (ensuring data validity) for the underlying numba-accelerated implementation, see :func:`simba.feature_extractors.perimeter_jit.jitted_hull`.
#
#     :param np.ndarray points: 3D array with shape (n_frames, n_body_parts, 2) containing [x, y] coordinates of body parts for each frame. Must contain non-negative pixel coordinates.
#     :param str target: Geometric property to calculate. Options: - 'perimeter': Calculate the perimeter (circumference) of the convex hull - 'area': Calculate the area enclosed by the convex hull. Default: 'perimeter'.
#     :return: Array with shape (n_frames,) containing the computed geometric property for each frame. Contains NaN values for frames where computation fails.
#     :rtype: np.ndarray
#
#     :example:
#     >>> points = np.random.randint(0, 500, size=(1000, 7, 2))
#     >>> get_hull_sizes(points=points)
#     """
#
#     check_valid_array(data=points, source=f'{get_hull_sizes.__name__} points', accepted_ndims=(3,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True)
#     check_str(name=f'{get_hull_sizes.__name__} target', options=('perimeter', 'area'), value=target, allow_blank=False, raise_error=True)
#     return jitted_hull(points=points.astype(np.float32), target=target).astype(np.float32)
#
#




# def bodypart_distance(bp1_coords: np.ndarray,
#                       bp2_coords: np.ndarray,
#                       px_per_mm: float = 1.0,
#                       in_centimeters: bool = False) -> np.ndarray:
#
#     """
#     Calculate frame-wise Euclidean distances between two sets of body part coordinates.
#
#     The function uses the standard Euclidean distance formula: distance = √((x₁-x₂)² + (y₁-y₂)²) / px_per_mm
#
#     .. seealso::
#        Wrapper function (ensuring data validity) for the underlying implementation :func:`simba.mixins.feature_extraction_mixin.FeatureExtractionMixin.framewise_euclidean_distance`.
#
#     :param np.ndarray bp1_coords: First body part coordinates with shape (n_frames, 2), where each row  contains [x, y] pixel coordinates for a specific frame.
#     :param np.ndarray bp2_coords: Second body part coordinates with shape (n_frames, 2), where each row  contains [x, y] pixel coordinates for a specific frame. Must have the same number of frames as bp1_coords.
#     :param float px_per_mm: Conversion factor from pixels to millimeters. Must be positive. Default: 1.0.
#     :param bool in_centimeters: If True, returns distances in centimeters. If False, returns distances in millimeters. Default: False.
#     :return: Array of Euclidean distances with shape (n_frames,) in the specified units as float32.
#     :rtype: np.ndarray[np.float32]
#
#     :example:
#     >>> bp1_coords = np.random.randint(0, 500, size=(1000, 2))
#     >>> bp2_coords = np.random.randint(0, 500, size=(1000, 2))
#     >>> bodypart_distance(bp1_coords=bp1_coords, bp2_coords=bp2_coords, px_per_mm=1.0, in_centimeters=False)
#     """
#
#     check_valid_array(data=bp1_coords, source=f'{bodypart_distance.__name__} bp1_coords', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True)
#     check_valid_array(data=bp2_coords, source=f'{bodypart_distance.__name__} bp2_coords', accepted_ndims=(2,), accepted_dtypes=Formats.NUMERIC_DTYPES.value, min_value=0.0, raise_error=True, accepted_axis_0_shape=(bp1_coords.shape[0],))
#     check_float(name=f'{bodypart_distance.__name__} px_per_mm', value=px_per_mm, min_value=10e-16, raise_error=True)
#     check_valid_boolean(value=in_centimeters, source=f'{bodypart_distance.__name__} px_per_mm', raise_error=True)
#
#     bp1_coords = bp1_coords.astype(np.float64)
#     bp2_coords = bp2_coords.astype(np.float64)
#     px_per_mm = np.float64(px_per_mm)
#     results = FeatureExtractionMixin.framewise_euclidean_distance(location_1=bp1_coords, location_2=bp2_coords, px_per_mm=px_per_mm, centimeter=in_centimeters)
#     return results.astype(np.float32)
#
#
#
#
#
# bp1_coords = np.random.randint(0, 500, size=(1000, 2))
# bp2_coords = np.random.randint(0, 500, size=(1000, 2))
# bodypart_distance(bp1_coords=bp1_coords, bp2_coords=bp2_coords, px_per_mm=1.0, in_centimeters=False)










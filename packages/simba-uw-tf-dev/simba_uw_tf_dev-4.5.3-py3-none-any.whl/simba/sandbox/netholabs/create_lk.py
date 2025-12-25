import pandas as pd
import os
from pathlib import Path
from typing import Union
import pickle

def get_video_frm_lk(data: Union[str, os.PathLike]) -> dict:
    df = pd.read_csv(data)
    df = df.drop(columns=["DATETIME"], errors="ignore")

    # Build ID map safely — only for columns with valid paths
    id_map = {}
    value_cols = []

    for col in df.columns:
        if col in ("UNIX_TIME", "DATETIME"):
            continue
        parts = Path(col).parts
        if len(parts) >= 2:
            id_map[col] = parts[-2]  # ID from path
            value_cols.append(col)   # Only keep valid path columns

    unix_times = df["UNIX_TIME"].values
    values = df[value_cols].values

    nested = {}

    for row_idx, unix_time in enumerate(unix_times):
        inner = {}
        for col_idx, col in enumerate(value_cols):
            id_key = id_map[col]
            inner.setdefault(id_key, {})[col] = values[row_idx, col_idx]
        nested[unix_time] = inner

    return nested






lk = get_video_frm_lk(data=r'D:\netholabs\temporal_stitching_2\test_temporal_stitching\test_2.csv')
with open(r'D:\netholabs\temporal_stitching_2\test_temporal_stitching\test_2.pk', 'wb') as f:
    pickle.dump(lk, f)
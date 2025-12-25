import pandas as pd
from pandas.core.dtypes.common import is_numeric_dtype
from typing import List, Dict, cast


def dataframe_to_dict(df: pd.DataFrame) -> List[Dict]:
    cols = list(df)
    col_arr_map = {}
    for col in cols:
        if not is_numeric_dtype(df[col].dtype):  # 如果是不是数字类型，使用numpy array存储
            col_arr_map[col] = df[col].to_numpy()
        else:
            col_arr_map[col] = df[col].tolist()  # 如果是数字类型，则使用python原生list存储
    records = [None] * len(df)

    for i in range(len(df)):
        record = {col: col_arr_map[col][i] for col in cols}
        records[i] = record

    return cast(List[Dict], records)

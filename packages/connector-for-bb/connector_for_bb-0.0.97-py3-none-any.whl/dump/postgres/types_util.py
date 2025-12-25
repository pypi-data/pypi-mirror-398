import datetime
from typing import Dict, Optional

import dateutil
import numpy as np
import pandas as pd
from pandas import DataFrame as PandasDataFrame


BOOL_MAPPER = {"f": False, "t": True}


def cast_df_by_schema(
    df: PandasDataFrame, schema: Dict[str, str], cast_timestamp: bool = True
) -> PandasDataFrame:
    for column in df.columns:
        if column in schema:
            cast_to = schema[column]["data_type"]
            try:
                if cast_to == "timestamp":
                    if cast_timestamp:
                        df[column] = pd.to_datetime(
                            df[column], errors="coerce", format="mixed"
                        )
                    continue

                if cast_to == "bool":
                    df[column] = df[column].apply(lambda x: BOOL_MAPPER.get(x, np.nan))

                df = df.astype({column: cast_to})
            except Exception as e:
                print(f"unable to cast column: {column} to {cast_to} error: {e}")
                pass
    df = df.replace("nan", np.nan)
    df = df.replace("None", np.nan)
    return df

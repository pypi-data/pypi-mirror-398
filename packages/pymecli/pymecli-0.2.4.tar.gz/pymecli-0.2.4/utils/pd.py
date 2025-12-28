import os
from typing import Literal

import pandas as pd
from pandas import DataFrame


def deduplicated(
    file_path: str,
    column_names: list[str],
    keep: Literal["first", "last"] = "last",
    pd_dtype: dict | None = None,
):
    if os.path.exists(file_path):
        existing_df: DataFrame = pd.read_csv(
            file_path, encoding="utf-8", dtype=pd_dtype
        )
        existing_df.drop_duplicates(subset=column_names, keep=keep, inplace=True)
        existing_df.to_csv(file_path, index=False, encoding="utf-8")
        return existing_df

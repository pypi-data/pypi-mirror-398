"""Functions for dataframe transformation."""

import pandas as pd


def batch_dataframe(df: pd.DataFrame, sizes: list[int]) -> list[pd.DataFrame]:
    """Split dataframe into batches of specified sizes.

    The last size is repeated until all rows are consumed.
    """
    batches = []
    start = 0
    size_idx = 0

    while start < len(df):
        size = sizes[min(size_idx, len(sizes) - 1)]
        end = start + size
        batches.append(df.iloc[start:end])
        start = end
        size_idx += 1

    return batches

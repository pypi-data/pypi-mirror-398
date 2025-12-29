from pathlib import Path
from typing import Literal

import pandas as pd
import polars as pl


def write_parquet(
    df: pd.DataFrame | pl.DataFrame,
    filepath: Path | str,
    *,
    index: bool = False,
    compression: Literal['lz4', 'uncompressed', 'snappy', 'gzip', 'brotli', 'zstd'] = 'zstd',
    compression_level: int = 3,
    **kwargs,
) -> None:
    """Write a DataFrame to a Parquet file.

    Parameters
    ----------
    df
        The DataFrame to write (pandas or polars).
    filepath
        The path to the output Parquet file.
    index
        Whether to write the DataFrame index (only for pandas DataFrames).
    compression
        The compression algorithm to use.
    compression_level
        The compression level to use.
    **kwargs
        Additional keyword arguments passed to the underlying write function.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(df, pd.DataFrame):
        return df.to_parquet(
            path=filepath,
            engine="pyarrow",
            compression=None if compression == 'uncompressed' else compression,
            compression_level=compression_level,
            index=index,
            **kwargs,
        )
    if isinstance(df, pl.DataFrame):
        return df.write_parquet(
            file=filepath,
            compression=compression,
            compression_level=compression_level,
            **kwargs,
        )
    raise TypeError(f"df must be a pandas or polars DataFrame, got {type(df)}")

import logging
import os
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def read_csv(
    filename: str,
    sep: str = ";",
    encoding="utf-8-sig",
    index_col: Optional[int] = None,
    **kwargs,
) -> pd.DataFrame:
    return pd.read_csv(filename, sep=sep, encoding=encoding, index_col=index_col, **kwargs)


def write_csv(
    df: pd.DataFrame,
    filename: str,
    sep: str = ";",
    encoding="utf-8-sig",
    index=False,
    verbose: bool = True,
    **kwargs,
):
    filename = os.path.realpath(filename)
    dir = os.path.dirname(os.path.realpath(filename))
    os.makedirs(dir, exist_ok=True)
    df.to_csv(filename, sep=sep, encoding=encoding, index=index, **kwargs)
    if verbose:
        logger.info(f"Data is written to {filename}.")


def append_csv(
    df: pd.DataFrame,
    filename: str,
    sep: str = ";",
    encoding="utf-8-sig",
    index=False,
    verbose: bool = True,
    **kwargs,
):
    filename = os.path.realpath(filename)
    dir = os.path.dirname(os.path.realpath(filename))
    os.makedirs(dir, exist_ok=True)
    if os.path.exists(filename):
        existing_df = read_csv(filename, sep=sep, encoding=encoding, **kwargs)
        df = pd.concat([existing_df, df], ignore_index=True)
    df.to_csv(filename, sep=sep, encoding=encoding, index=index, **kwargs)
    if verbose:
        logger.info(f"Data is appended to {filename}.")

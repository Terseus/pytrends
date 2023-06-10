from __future__ import annotations


import pandas as pd

from .framework.repl import DataFrameAssertionError


def assert_frame_equal(df_result: pd.DataFrame, df_expected: pd.DataFrame, **kwargs) -> None:
    try:
        pd.testing.assert_frame_equal(df_result, df_expected, **kwargs)
    except AssertionError as error:
        raise DataFrameAssertionError(df_result, df_expected, error) from error

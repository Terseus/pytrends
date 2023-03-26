import pandas as pd


class DataFrameAssertionError(AssertionError):
    df_left: pd.DataFrame
    df_right: pd.DataFrame

    def __init__(self, df_left: pd.DataFrame, df_right: pd.DataFrame, source: Exception) -> None:
        self.df_left = df_left
        self.df_right = df_right
        super().__init__(*source.args)


def assert_frame_equal(df_left: pd.DataFrame, df_right: pd.DataFrame, **kwargs) -> None:
    try:
        pd.testing.assert_frame_equal(df_left, df_right, **kwargs)
    except AssertionError as error:
        raise DataFrameAssertionError(df_left, df_right, error) from error

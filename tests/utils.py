import pandas as pd


class DataFrameAssertionError(AssertionError):
    df_left: pd.DataFrame
    df_right: pd.DataFrame

    def __init__(self, df_left: pd.DataFrame, df_right: pd.DataFrame, source: Exception) -> None:
        self.df_left = df_left
        self.df_right = df_right
        super().__init__(*source.args)

    def get_diff(self, complete=False) -> pd.DataFrame:
        df_diff = self.df_left.compare(
            self.df_right,
            keep_shape=complete,
            keep_equal=complete,
        )
        # `result_names` is not available until Pandas 1.5 so we implement it manually.
        df_names_map = {
            'self': 'result',
            'other': 'expected',
        }
        df_diff = df_diff.rename(
            lambda column: df_names_map.get(column, column),
            axis='columns'
        )
        return df_diff


def assert_frame_equal(df_left: pd.DataFrame, df_right: pd.DataFrame, **kwargs) -> None:
    try:
        pd.testing.assert_frame_equal(df_left, df_right, **kwargs)
    except AssertionError as error:
        raise DataFrameAssertionError(df_left, df_right, error) from error

import pandas as pd


class DataFrameAssertionError(AssertionError):
    df_result: pd.DataFrame
    df_expected: pd.DataFrame

    def __init__(self, df_result: pd.DataFrame, df_expected: pd.DataFrame, source: Exception) -> None:
        self.df_result = df_result
        self.df_expected = df_expected
        super().__init__(*source.args)

    def get_diff(self, complete=False) -> pd.DataFrame:
        df_diff = self.df_result.compare(
            self.df_expected,
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

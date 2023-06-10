from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pytest import Item
import pandas as pd
import pytest

from .repl import Repl


BASE_PATH = Path("tests") / "dataframes"


@dataclass
class DataFrameCassette:
    df: pd.DataFrame
    file_path: Path
    item: Item

    def assert_equals_to(self, df_other: pd.DataFrame, **kwargs) -> None:
        try:
            pd.testing.assert_frame_equal(self.df, df_other, **kwargs)
        except AssertionError as error:
            with Repl.capsys_disabled(item=self.item, df_result=df_other,
                                      df_expected=self.df, error=error) as repl:
                repl.start_loop()

    def replace(self, df_new: pd.DataFrame) -> DataFrameCassette:
        df_new.to_json(self.file_path, orient="table")
        return type(self)(
            df=df_new,
            file_path=self.file_path,
            item=self.item
        )

    @classmethod
    def from_item(cls, item: pytest.Item) -> DataFrameCassette:
        file_path = BASE_PATH / f"df_expected_{item.name}.json"
        dataframe = pd.read_json(file_path, orient="table")
        return cls(dataframe, file_path, item)

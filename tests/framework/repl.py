from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, ContextManager

from vcr import VCR
import pandas as pd
import pytest
from _pytest.capture import CaptureManager


DATAFRAMES_PATH = Path("dataframes")


def get_item_df_cassette(item: pytest.Item) -> Path:
    return DATAFRAMES_PATH / f"df_expected_{item.name}.json"


@contextmanager
def capsys_disabled(config: pytest.Config) -> None:
    """
    Disable capsys capture of stdout, stderr *and* stdin inside the context.
    """
    capman: CaptureManager = config.pluginmanager.getplugin("capturemanager")
    try:
        capman.suspend_global_capture(in_=True)
        yield
    finally:
        capman.resume_global_capture()


def _get_df_diff(
    df_result: pd.DataFrame,
    df_expected: pd.DataFrame,
    complete: bool = False
) -> pd.DataFrame:
    df_diff = df_result.compare(
        df_expected,
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


@dataclass
class _ReplOption:
    trigger: str
    text: str
    handler: Callable[[], None]


class InvalidReplOptionError(RuntimeError):
    pass


class StopRepl(RuntimeError):
    pass


class Repl:
    def __init__(
        self,
        item: pytest.Item,
        df_result: pd.DataFrame,
        df_expected: pd.DataFrame,
        error: Exception
    ) -> None:
        self._item = item
        self._df_result = df_result
        self._df_expected = df_expected
        self._error = error
        self._options = (
            _ReplOption("R", "show (R)esult", self._handler_show_result),
            _ReplOption("E", "show (E)xpected", self._handler_show_expected),
            _ReplOption("D", "show (D)iff", self._handler_show_diff),
            _ReplOption("F", "show (F)ull diff", self._handler_show_full_diff),
            _ReplOption("A", "(A)ccept new result", self._handler_accept),
            _ReplOption("C", "(C)ancel", self._handler_cancel),
        )
        options_text = ", ".join(option.text for option in self._options)
        self._prompt = f"[{options_text}] "

    def _resolve_input(self, value: str) -> _ReplOption:
        trigger = value.upper()
        if len(trigger) > 1:
            trigger = trigger[0]
        for option in self._options:
            if trigger == option.trigger:
                return option
        raise InvalidReplOptionError(f"Option not found: {value}")

    def _handler_void(self) -> None:
        print("##### NOT IMPLEMENTED #####")
        pass

    def _print_title(self, text: str) -> None:
        print(f"===== {text} =====")

    def _handler_show_result(self) -> None:
        self._print_title("Result DataFrame")
        print(self._df_result)

    def _handler_cancel(self) -> None:
        self._print_title("Cancel")
        raise

    def _handler_show_expected(self) -> None:
        self._print_title("Expected DataFrame")
        print(self._df_expected)

    def _handler_show_diff(self) -> None:
        self._print_title("Result & Expected diff")
        print(_get_df_diff(self._df_result, self._df_expected))

    def _handler_show_full_diff(self) -> None:
        self._print_title("Result & Expected full diff")
        print(_get_df_diff(self._df_result, self._df_expected, complete=True))

    def _handler_accept(self) -> None:
        self._print_title("Accept new result")
        file_dataframe = get_item_df_cassette(self._item)
        self._df_result.to_json(
            file_dataframe,
            orient='table',
            indent=2
        )
        cassette: VCR = self._item._request.getfixturevalue("vcr")
        cassette.rewind()
        if not cassette.write_protected:
            cassette.data.clear()
        raise StopRepl()

    def start_loop(self) -> None:
        print("\n")
        self._print_title(f"Test DataFrame for {self._item.name}")
        print(self._error)
        while True:
            print("\nChoose an option:")
            result = input(self._prompt)
            try:
                option = self._resolve_input(result)
            except InvalidReplOptionError:
                print("Invalid option: ", result)
                continue
            option.handler()

    @classmethod
    @contextmanager
    def capsys_disabled(cls, item: pytest.Item, **kwargs) -> ContextManager[Repl]:
        kwargs["item"] = item
        with capsys_disabled(item.config):
            yield Repl(**kwargs)

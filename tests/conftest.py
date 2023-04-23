from pathlib import Path
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from typing import Callable

from _pytest.fixtures import SubRequest
from _pytest.capture import CaptureManager
import pytest
from responses import RequestsMock
import pandas as pd

from .utils import DataFrameAssertionError


DATAFRAMES_PATH = Path(".") / 'tests' / 'dataframes'


@dataclass
class _ReplOption:
    trigger: str
    text: str
    handler: Callable[[], None]


class InvalidReplOptionError(RuntimeError):
    pass


class StopRepl(RuntimeError):
    pass


class _Repl:
    def __init__(self, item: pytest.Item, error: DataFrameAssertionError) -> None:
        self._item = item
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
        print(self._error.df_left)

    def _handler_cancel(self) -> None:
        self._print_title("Cancel")
        raise

    def _handler_show_expected(self) -> None:
        self._print_title("Expected DataFrame")
        print(self._error.df_right)

    def _handler_show_diff(self) -> None:
        self._print_title("Result & Expected diff")
        print(self._error.get_diff())

    def _handler_show_full_diff(self) -> None:
        self._print_title("Result & Expected full diff")
        print(self._error.get_diff(complete=True))

    def _handler_accept(self) -> None:
        self._print_title("Accept new result")
        file_dataframe = _get_item_df_cassette(self._item)
        self._error.df_left.to_json(
            file_dataframe,
            orient='table',
            indent=2
        )
        # TODO: ¿Cómo repetir el test después de modificar el cassette del test?
        # Ahora mismo si no hago nada el test falla de todos modos.
        # Aunque borre los campos de sys, sigue fallando
        # import sys
        # del sys.last_type
        # del sys.last_value
        # del sys.last_traceback
        # Aunque llame a teardown y setup, sigue fallando; no recarga las fixtures
        # self._item.teardown()
        # self._item.setup()
        # self._item.runtest()
        raise StopRepl()

    def start_loop(self) -> None:
        print("\n")
        self._print_title(f"Test DataFrame for {self._item.name}")
        print(self._error)
        while True:
            print("Choose an option:")
            result = input(self._prompt)
            try:
                option = self._resolve_input(result)
            except InvalidReplOptionError:
                print("Invalid option: ", result)
                continue
            option.handler()


@contextmanager
def _capsys_disabled(config: pytest.Config) -> None:
    """
    Disable capsys capture of stdout, stderr *and* stdin inside the context.
    """
    capman: CaptureManager = config.pluginmanager.getplugin("capturemanager")
    try:
        capman.suspend_global_capture(in_=True)
        yield
    finally:
        capman.resume_global_capture()


def _get_item_df_cassette(item: pytest.Item) -> Path:
    return DATAFRAMES_PATH / f"df_expected_{item.name}.json"


def _dataframe_assertion_error_repl(
    item: pytest.Item,
    error: DataFrameAssertionError,
) -> None:
    print(error)
    print("========== Differences ==========")
    print(error.get_diff())
    while True:
        print("Choose an option:")
        result = input(
            "["
            "show (R)esult, "
            "show (E)xpected, "
            "show (F)ull diff, "
            "(A)ccept new result, "
            "(C)ancel)"
            "]: "
        )
        return result


@pytest.fixture
def mocked_responses():
    """
    A pre-configured `RequestsMock` instance to write tests which mocks the backend
    responses.
    """
    requests_mock = RequestsMock(
        assert_all_requests_are_fired=True
    )
    with requests_mock as mocked_responses:
        yield mocked_responses


@pytest.fixture
def df_expected_NEW(request: SubRequest) -> pd.DataFrame:
    file_dataframe = _get_item_df_cassette(request.node)
    dataframe = pd.read_json(file_dataframe, orient='table')
    return dataframe


def pytest_runtest_call(item: pytest.Item) -> None:
    if "df_expected_NEW" not in item.fixturenames:
        return item.runtest()
    try:
        item.runtest()
    except DataFrameAssertionError as error:
        repl = _Repl(item, error)
        with _capsys_disabled(item.config):
            with suppress(StopRepl):
                repl.start_loop()

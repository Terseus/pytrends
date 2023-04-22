from pathlib import Path
from contextlib import contextmanager

from _pytest.fixtures import SubRequest
from _pytest.capture import CaptureManager
import pytest
from responses import RequestsMock
import pandas as pd

from .utils import DataFrameAssertionError


DATAFRAMES_PATH = Path(".") / 'tests' / 'dataframes'
DATAFRAMES_MARKER = "dataframe_cassette"


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
    test_name = request.node.name
    file_dataframe = DATAFRAMES_PATH / f"df_expected_{test_name}.json"
    dataframe = pd.read_json(file_dataframe, orient='table')
    request.node.add_marker(getattr(pytest.mark, DATAFRAMES_MARKER)(file_dataframe))
    return dataframe


def pytest_runtest_call(item: pytest.Item) -> None:
    marker = item.get_closest_marker(DATAFRAMES_MARKER)
    if marker is None:
        return item.runtest()
    try:
        item.runtest()
    except DataFrameAssertionError as error:
        err = error
        # with capman.global_and_fixture_disabled():
        # breakpoint()
        # pass
        # result = input("It failed!: ")
        # print("Readed: ", result)
        with capsys_disabled(item.config):
            result = input("\nTesting...")
            print("Readed: ", result)
        raise

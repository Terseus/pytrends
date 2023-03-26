from pathlib import Path

from _pytest.fixtures import SubRequest
import pytest
from responses import RequestsMock
import pandas as pd


DATAFRAMES_PATH = Path(".") / 'tests' / 'dataframes'


@pytest.fixture
def mocked_responses():
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
    return dataframe

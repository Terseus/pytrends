from contextlib import suppress
from typing import Callable

from _pytest.fixtures import SubRequest
import pytest
from responses import RequestsMock
import pandas as pd

# from .utils import capsys_disabled
# from .framework.repl import Repl, StopRepl, get_item_df_cassette, DataFrameAssertionError
from .framework.dataframe_cassette import DataFrameCassette


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


# @pytest.fixture
# def df_loader(request: SubRequest) -> Callable[[], pd.DataFrame]:
#     def loader() -> pd.DataFrame:
#         file_dataframe = get_item_df_cassette(request.node)
#         dataframe = pd.read_json(file_dataframe, orient='table')
#         return dataframe
#     return loader


@pytest.fixture
def df_cassette(request: SubRequest) -> DataFrameCassette:
    instance = DataFrameCassette.from_item(request.node)
    return instance


# TODO: Nuevo plan: hacer que la fixture devuelva un objeto que se encargue de la
# comparación, manejar la excepción, comparar con el DataFrame nuevo, etc.
# De esta forma eliminamos la complejidad inherente de intentar extender pytest.
# Debería ser más robusto y fácil de mantener, aunque resulte un poco raro.
# Si además hacemos que la fixture sea un proxy del DataFrame que envuelve sería ya la
# ostia.
# @pytest.hookimpl(hookwrapper=True)
# def pytest_runtest_call(item: pytest.Item) -> None:
#     breakpoint()
#     pass
#     try:
#         yield
#     except DataFrameAssertionError as error:
#         breakpoint()
#         repl = Repl(item, error)
#         with capsys_disabled(item.config):
#             with suppress(StopRepl):
#                 repl.start_loop()
#             return pytest_runtest_call(item)

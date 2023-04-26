from __future__ import annotations

from contextlib import contextmanager

from _pytest.capture import CaptureManager
import pandas as pd
import pytest

from .framework.repl import DataFrameAssertionError


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


def assert_frame_equal(df_result: pd.DataFrame, df_expected: pd.DataFrame, **kwargs) -> None:
    try:
        pd.testing.assert_frame_equal(df_result, df_expected, **kwargs)
    except AssertionError as error:
        raise DataFrameAssertionError(df_result, df_expected, error) from error

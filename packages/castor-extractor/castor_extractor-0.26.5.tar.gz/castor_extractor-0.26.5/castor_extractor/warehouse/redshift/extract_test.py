import pytest

from .extract import (
    REDSHIFT_SERVERLESS,
    _query_builder,
)


@pytest.mark.parametrize(
    "serverless_param,env_param,expected",
    [
        (True, "False", True),
        (False, "True", True),
        (None, "TRUE", True),
        (None, "TrUe", True),
        (None, "FAlSE", False),
        (None, "False", False),
        (None, None, False),
        (True, None, True),
    ],
)
def test__query_builder(serverless_param, env_param, expected, monkeypatch):
    params = {"serverless": serverless_param}
    monkeypatch.setenv(REDSHIFT_SERVERLESS, env_param)

    assert _query_builder(params).is_serverless == expected

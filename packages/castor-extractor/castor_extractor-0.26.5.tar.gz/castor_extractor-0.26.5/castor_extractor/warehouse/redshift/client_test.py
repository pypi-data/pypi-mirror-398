"""https://www.notion.so/castordoc/Workshop-Mocking-405ef02712e6446193720abf8d4c2f53"""

from unittest.mock import Mock, patch

from .client import RedshiftClient
from .query import ExtractionQuery

RESULT = [{"foo": "bar"}]
CASTOR_EXTRACTOR_PATH = "source.packages.extractor.castor_extractor"


def fake_execute(statement: str, params: dict):
    return RESULT


@patch.object(RedshiftClient, "_build_uri")
@patch.object(RedshiftClient, "_engine_options")
@patch(f"{CASTOR_EXTRACTOR_PATH}.utils.client.abstract.create_engine")
@patch.object(RedshiftClient, "close")
@patch.object(RedshiftClient, "connect")
def test_redshift_client_execute(
    mock_connect,
    mock_close,
    mock_create_engine,
    mock_engine_options,
    mock_build_uri,
):
    mock_connect.return_value = Mock(execute=fake_execute)

    credentials = {}
    client = RedshiftClient(credentials)
    query = ExtractionQuery("toto", {"option": 1})

    res = client.execute(query)

    assert list(res) == RESULT

    mock_close.assert_called_once()

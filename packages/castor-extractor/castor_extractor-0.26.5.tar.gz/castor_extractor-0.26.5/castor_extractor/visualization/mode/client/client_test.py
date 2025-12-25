import json

from ....utils import load_file
from ..assets import EXPORTED_FIELDS, ModeAnalyticsAsset
from .client import Client, ModeCredentials

_HOST = "https://mode.com"
_WORKSPACE = "castor"


def _dummy_client() -> Client:
    credentials = ModeCredentials(
        host=_HOST,
        workspace=_WORKSPACE,
        token="dummy-token",
        secret="******",
    )
    return Client(credentials=credentials)


def test__url():
    client = _dummy_client()
    # basic calls
    value_1 = client._url(resource_name="spaces")
    assert value_1 == f"{_HOST}/api/{_WORKSPACE}/spaces"

    # with spaces
    value_2 = client._url(space="123456789", resource_name="reports")
    assert value_2 == f"{_HOST}/api/{_WORKSPACE}/spaces/123456789/reports"

    # with report
    value_3 = client._url(report="xxx", resource_name="queries")
    assert value_3 == f"{_HOST}/api/{_WORKSPACE}/reports/xxx/queries"

    # without workspace
    value_4 = client._url(resource_name="john_doe", with_workspace=False)
    assert value_4 == f"{_HOST}/api/john_doe"


def test__post_processing():
    client = _dummy_client()
    raw = load_file("client_test.json", __file__)
    result = client._post_processing(
        asset=ModeAnalyticsAsset.COLLECTION,
        data=[json.loads(raw)],
    )
    collection = result[0]
    assert set(collection.keys()) == set(
        EXPORTED_FIELDS[ModeAnalyticsAsset.COLLECTION],
    )
    assert collection["creator"] == "john_doe"

from .api_client import DatabricksAPIClient


class MockDatabricksClient(DatabricksAPIClient):
    def __init__(self):
        self._db_allowed = ["prd", "staging"]
        self._db_blocked = ["dev"]


def test_DatabricksAPIClient__keep_catalog():
    client = MockDatabricksClient()
    assert client._keep_catalog("prd")
    assert client._keep_catalog("staging")
    assert not client._keep_catalog("dev")
    assert not client._keep_catalog("something_unknown")

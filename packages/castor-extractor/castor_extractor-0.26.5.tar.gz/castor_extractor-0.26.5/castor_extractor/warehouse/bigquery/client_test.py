"""https://www.notion.so/castordoc/Workshop-Mocking-405ef02712e6446193720abf8d4c2f53"""

from typing import NamedTuple
from unittest.mock import Mock

from .client import BigQueryClient


class MockProject(NamedTuple):
    project_id: str


class MockDataset(NamedTuple):
    dataset_id: str


client_project_structure = {
    "project_1": [MockDataset("dataset_1"), MockDataset("dataset_2")],
    "project_2": [MockDataset("dataset_3"), MockDataset("hidden_dataset")],
    "hidden_project": [MockDataset("dataset_h1"), MockDataset("dataset_h2")],
}


class MockBigQueryClient(BigQueryClient):
    def __init__(self):
        self._db_allowed = ["project_2", "project_1"]
        self._dataset_blocked = ["hidden_dataset"]
        self._db_blocked = ["hidden_project"]
        self._projects = None
        self._datasets = None
        self.client = self._client()

    def _client(self) -> Mock:
        fake_client = Mock()
        fake_client.list_projects = Mock(
            return_value=[
                MockProject("project_1"),
                MockProject("project_2"),
                MockProject("hidden_project"),
            ],
        )
        fake_client.list_datasets = lambda project: client_project_structure[
            project
        ]
        return fake_client


def test_bigquery_client__list_datasets():
    client = MockBigQueryClient()
    assert client._list_datasets() == [
        MockDataset("dataset_1"),
        MockDataset("dataset_2"),
        MockDataset("dataset_3"),
    ]

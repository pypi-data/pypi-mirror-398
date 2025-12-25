import pytest

from .credentials import StrategyCredentials


def test_StrategyCredentials_project_ids():
    creds = {
        "base_url": "https://demo.strategy.com/MicroStrategyLibrary/api",
        "username": "castor",
        "password": "ilovepotatoes",
        "visualization_type": "strategy",
    }

    # no project IDs
    StrategyCredentials(**creds)

    # list of project IDs
    project_ids = ["ID1", "ID2", "ID3"]
    creds_using_list = {**creds, "project_ids": project_ids}
    credentials = StrategyCredentials(**creds_using_list)
    assert credentials.project_ids == project_ids

    # list of comma-separated of project IDs
    creds_using_comma_separated_ids = {**creds, "project_ids": " ID1 ,ID2, ID3"}
    credentials = StrategyCredentials(**creds_using_comma_separated_ids)
    assert credentials.project_ids == project_ids

    # single project ID string
    creds_using_single_id_string = {**creds, "project_ids": "ID1"}
    credentials = StrategyCredentials(**creds_using_single_id_string)
    assert credentials.project_ids == ["ID1"]

    with pytest.raises(ValueError):
        creds_with_unsupported_type = {**creds, "project_ids": 123456}
        StrategyCredentials(**creds_with_unsupported_type)

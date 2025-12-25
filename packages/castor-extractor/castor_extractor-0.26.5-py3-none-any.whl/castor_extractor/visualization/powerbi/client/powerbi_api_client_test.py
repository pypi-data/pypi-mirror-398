from datetime import date
from unittest.mock import Mock, call, patch

import pytest

from .authentication import msal
from .client import PowerBIAPIClient
from .constants import Keys
from .credentials import CLIENT_APP_BASE, REST_API_BASE_PATH, PowerbiCredentials
from .endpoints import PowerBiEndpointFactory

FAKE_TENANT_ID = "IamFake"
FAKE_CLIENT_ID = "MeTwo"
FAKE_SECRET = "MeThree"

ENDPOINT_FACTORY = PowerBiEndpointFactory(
    login_url=CLIENT_APP_BASE,
    api_base=REST_API_BASE_PATH + "/",  # superfluous "/" to test resiliency
)


@pytest.fixture
def mock_msal():
    with patch.object(msal, "ConfidentialClientApplication") as mock_app:
        mock_app.return_value.acquire_token_for_client.return_value = {
            "access_token": "fake_token"
        }
        yield mock_app


@pytest.fixture
def power_bi_client(mock_msal):
    creds = PowerbiCredentials(
        tenant_id=FAKE_TENANT_ID,
        client_id=FAKE_CLIENT_ID,
        secret=FAKE_SECRET,
    )
    return PowerBIAPIClient(creds)


def test__access_token(power_bi_client, mock_msal):
    # Valid token scenario
    valid_token = "mock_token"
    mock_response = {"access_token": valid_token}
    returning_valid_token = Mock(return_value=mock_response)
    mock_msal.return_value.acquire_token_for_client = returning_valid_token

    assert power_bi_client._auth.fetch_token() == valid_token

    # Invalid token scenario
    invalid_response = {"not_access_token": "666"}
    returning_invalid_token = Mock(return_value=invalid_response)
    mock_msal.return_value.acquire_token_for_client = returning_invalid_token

    with pytest.raises(ValueError):
        power_bi_client._auth.fetch_token()


def test__datasets(power_bi_client):
    with patch.object(power_bi_client, "_get") as mocked_get:
        mocked_get.return_value = {"value": [{"id": 1, "type": "dataset"}]}
        datasets = list(power_bi_client.datasets())
        mocked_get.assert_called_with(ENDPOINT_FACTORY.datasets())
        assert datasets == [{"id": 1, "type": "dataset"}]


def test__dashboards(power_bi_client):
    with patch.object(power_bi_client, "_get") as mocked_get:
        mocked_get.return_value = {"value": [{"id": 1, "type": "dashboard"}]}
        dashboards = list(power_bi_client.dashboards())
        mocked_get.assert_called_with(ENDPOINT_FACTORY.dashboards())
        assert dashboards == [{"id": 1, "type": "dashboard"}]


def test__reports(power_bi_client):
    report_1 = {"id": 1, "type": "report", "workspaceId": "1"}
    report_2 = {"id": 2, "type": "report", "workspaceId": "no access"}
    workspace = {"id": "1"}
    page = {"name": "page_name", "displayName": "page", "order": 0}

    with patch.object(power_bi_client, "_get") as mocked_get:
        mocked_get.side_effect = [
            {"value": [report_1, report_2]},  # reports
            {"value": [workspace]},  # accessible workspaces
            {"value": [page]},  # pages
        ]
        reports = list(power_bi_client.reports())
        calls = [
            call(ENDPOINT_FACTORY.reports()),
            call(ENDPOINT_FACTORY.groups()),
            call(ENDPOINT_FACTORY.pages("1"), retry_on_timeout=False),
        ]
        mocked_get.assert_has_calls(calls)
        assert reports == [
            {**report_1, "pages": [page]},
            report_2,
        ]


def test__workspace_ids(power_bi_client):
    with patch.object(power_bi_client, "_get") as mocked_get:
        mocked_get.return_value = [{"id": 1000}, {"id": 1001}, {"id": 1003}]

        ids = power_bi_client._workspace_ids()
        assert ids == [1000, 1001, 1003]

        params = {
            Keys.INACTIVE_WORKSPACES: True,
            Keys.PERSONAL_WORKSPACES: True,
        }

        mocked_get.assert_called_with(
            ENDPOINT_FACTORY.workspace_ids(),
            params=params,
        )


@patch.object(PowerBIAPIClient, "_get_scan_result")
@patch.object(PowerBIAPIClient, "_wait_for_scan_result")
@patch.object(PowerBIAPIClient, "_create_scan")
@patch.object(PowerBIAPIClient, "_workspace_ids")
def test__metadata(
    mock_workspace_ids,
    mock_create_scan,
    mock_wait_for_scan,
    mock_get_scan_result,
    power_bi_client,
):
    mock_workspace_ids.return_value = list(range(200))
    mock_create_scan.return_value = 314
    mock_wait_for_scan.return_value = True
    mock_get_scan_result.return_value = [{"workspace_id": 1871}]

    result = list(power_bi_client.metadata())

    assert result == [{"workspace_id": 1871}, {"workspace_id": 1871}]


def test__activity_events(power_bi_client):
    day = date.today()
    mocked_get_results = [
        {
            Keys.ACTIVITY_EVENT_ENTITIES: [
                {
                    "id": "foo",
                    "name": "Foo",
                    "ClientIP": "1.1.1.1",
                    "UserAgent": "Mozilla/5.0",
                },
                {
                    "id": "bar",
                    "name": "Bar",
                    "ClientIP": "1.1.1.2",
                    "UserAgent": "Mozilla/5.0",
                },
            ],
            Keys.LAST_RESULT_SET: False,
            Keys.CONTINUATION_URI: "https://next-call-1",
        },
        {
            Keys.ACTIVITY_EVENT_ENTITIES: [
                {
                    "id": "baz",
                    "name": "Baz",
                    "ClientIP": "1.1.1.3",
                    "UserAgent": "Mozilla/5.0",
                }
            ],
            Keys.LAST_RESULT_SET: False,
            Keys.CONTINUATION_URI: "https://next-call-2",
        },
        {
            Keys.ACTIVITY_EVENT_ENTITIES: [
                {
                    "id": "biz",
                    "name": "Biz",
                    "ClientIP": "1.1.1.4",
                    "UserAgent": "Mozilla/5.0",
                }
            ],
            Keys.LAST_RESULT_SET: True,
            Keys.CONTINUATION_URI: None,
        },
    ]

    with patch.object(power_bi_client, "_get") as mocked_get:
        mocked_get.side_effect = mocked_get_results

        result = list(power_bi_client.activity_events(day=day))
        assert result == [
            {"id": "foo", "name": "Foo"},
            {"id": "bar", "name": "Bar"},
            {"id": "baz", "name": "Baz"},
            {"id": "biz", "name": "Biz"},
        ]

        expected_calls = [
            call(endpoint=ENDPOINT_FACTORY.activity_events(day=day)),
            call(endpoint="https://next-call-1"),
            call(endpoint="https://next-call-2"),
        ]
        mocked_get.assert_has_calls(expected_calls)

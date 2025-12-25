import datetime
from unittest.mock import patch

import pytest
from castor_extractor.visualization.looker.api.client import (  # type: ignore
    ApiClient,
)
from castor_extractor.visualization.looker.api.credentials import (  # type: ignore
    LookerCredentials,
)
from dateutil.utils import today
from freezegun import freeze_time

from .client import _mondays


def _credentials():
    return LookerCredentials(  # noqa: S106
        base_url="base_url",
        client_id="client_id",
        client_secret="secret",
    )


@patch("castor_extractor.visualization.looker.api.client.init40")
@patch("castor_extractor.visualization.looker.api.client.has_admin_permissions")
def test_api_client_has_admin_permissions(
    mock_has_admin_permission,
    mock_init40,
):
    mock_has_admin_permission.return_value = False
    with pytest.raises(PermissionError):
        ApiClient(_credentials())

    mock_has_admin_permission.return_value = True
    mock_init40.return_value = "sdk"
    client = ApiClient(_credentials())
    assert client._sdk == "sdk"


@freeze_time("2023-7-4")
def test__mondays():
    expected_30_days = {
        datetime.date(2023, 7, 3),
        datetime.date(2023, 6, 26),
        datetime.date(2023, 6, 19),
        datetime.date(2023, 6, 12),
        datetime.date(2023, 6, 5),
    }
    assert set(_mondays(history_depth_in_days=30)) == expected_30_days

    # only mondays
    assert all([day.weekday() == 0 for day in _mondays(30)])
    assert all([day.weekday() == 0 for day in _mondays(100)])

    # all days must remain in the elapsed history
    history_days = 1_000
    end = today().date()
    start = end - datetime.timedelta(days=history_days)
    output = _mondays(history_depth_in_days=history_days)

    assert all([day >= start for day in output])
    assert all([day < end for day in output])

    with pytest.raises(AssertionError):
        list(_mondays(history_depth_in_days=0))
        list(_mondays(history_depth_in_days=-5))

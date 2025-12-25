import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from dateutil.tz import tzutc

from .client import ContentType, DbtClient, DbtRun, _account_url  # type: ignore
from .credentials import DbtCredentials

_DBT_CLIENT_PATH = "source.packages.extractor.castor_extractor.transformation.dbt.client.DbtClient"
_OLD_DATE = datetime(2023, 7, 10, 12, 6, 23, 109171, tzinfo=tzutc())
_OLD_DATE_STR = "2023-07-10 12:06:23.109171+00:00"
_RECENT_DATE = datetime(2023, 10, 6, 5, 9, 31, 731991, tzinfo=tzutc())
_RECENT_DATE_STR = "2023-10-06 05:09:31.731991+00:00"


def _assert_called_with(
    mocked_call: MagicMock,
    job_id: int | str,
    date_range: tuple[datetime, datetime] | None = None,
) -> None:
    url = "https://cloud.getdbt.com/api/v2/accounts/40/runs/"
    params = {
        "job_definition_id": job_id,
        "limit": 1,
        "order_by": "-finished_at",
        "status": 10,
    }
    if date_range:
        params["finished_at__range"] = json.dumps(
            [d.isoformat() for d in date_range]
        )
    mocked_call.assert_called_with(url, params)


def test_DbtClient_last_run():
    default_job_id = "123"
    now = datetime.now()
    two_days_ago = now - timedelta(days=2)

    infer_path = f"{_DBT_CLIENT_PATH}._infer_account_id"
    call_path = f"{_DBT_CLIENT_PATH}._call"

    mock_response_default_job = [{"id": 1, "finished_at": _OLD_DATE_STR}]
    mock_response_job_42 = [{"id": 2, "finished_at": _RECENT_DATE_STR}]

    with patch(infer_path, return_value="40"), patch(call_path) as mocked_call:
        credentials = DbtCredentials(token="some-token", job_id=default_job_id)

        dbt_client = DbtClient(credentials=credentials)

        # default job ID, no range
        mocked_call.return_value = mock_response_default_job
        result = dbt_client.last_run()
        assert result == DbtRun(id=1, finished_at=_OLD_DATE)
        _assert_called_with(mocked_call, default_job_id)

        # given job ID, no range
        mocked_call.return_value = mock_response_job_42
        result = dbt_client.last_run(job_id=42)
        assert result == DbtRun(id=2, finished_at=_RECENT_DATE)
        _assert_called_with(mocked_call, 42)

        # with range, empty response
        mocked_call.return_value = None
        result = dbt_client.last_run(finished_at_range=(two_days_ago, now))
        assert result is None
        _assert_called_with(mocked_call, default_job_id, (two_days_ago, now))

        # results array returned, but dict is None (shouldn't happen but who knows)
        mocked_call.return_value = [None]
        with pytest.raises(ValueError):
            dbt_client.last_run()


def test_DbtClient_list_job_identifiers():
    infer_path = f"{_DBT_CLIENT_PATH}._infer_account_id"
    call_path = f"{_DBT_CLIENT_PATH}._call"

    jobs = [
        {"id": 23, "state": 1},
        {"id": 46, "state": 2},  # deleted
        {"id": 395, "state": 1},
    ]

    with patch(infer_path, return_value="40"), patch(call_path) as mocked_call:
        mocked_call.return_value = jobs
        credentials = DbtCredentials(token="some-token", job_id="1")
        dbt_client = DbtClient(credentials=credentials)

        jobs_ids = dbt_client.list_job_identifiers()
        assert jobs_ids == {23, 395}


def test_DbtClient_fetch_artifacts():
    infer_path = f"{_DBT_CLIENT_PATH}._infer_account_id"
    call_path = f"{_DBT_CLIENT_PATH}._call"
    run_id = 12345
    url = "https://cloud.getdbt.com/api/v2/accounts/40/runs/{}/artifacts/{}"

    with patch(infer_path, return_value="40"), patch(call_path) as mocked_call:
        credentials = DbtCredentials(token="some-token", job_id="1")
        dbt_client = DbtClient(credentials=credentials)

        dbt_client.fetch_run_results(run_id)
        mocked_call.assert_called_with(
            url.format(run_id, "run_results.json"),
            content_type=ContentType.TEXT,
            ignore_not_found=True,
        )

        mocked_call.reset_mock()

        dbt_client.fetch_manifest(run_id)
        mocked_call.assert_called_with(
            url.format(run_id, "manifest.json"),
            content_type=ContentType.TEXT,
            ignore_not_found=False,
        )


def test___account_url():
    base_url = "https://cloud.getdbt.com"
    assert _account_url(base_url) == "https://cloud.getdbt.com/api/v2/accounts/"

    base_url = "https://emea.dbt.com/"
    assert _account_url(base_url) == "https://emea.dbt.com/api/v2/accounts/"

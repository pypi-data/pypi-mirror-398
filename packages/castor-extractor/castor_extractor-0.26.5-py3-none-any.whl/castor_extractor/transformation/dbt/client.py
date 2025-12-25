import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal

import requests
from dateutil.parser import parse

from ...utils.url import add_path
from .credentials import DbtCredentials

logger = logging.getLogger(__name__)


_URL_SUFFIX = "/api/v2/accounts/"

_DATA_KEY = "data"
_SUCCESSFUL_RUN_STATUS = 10
_DELETED_JOB_STATE = 2

Artifact = Literal["manifest.json", "run_results.json"]


class ContentType(Enum):
    JSON = "application/json"
    TEXT = "text/html"


@dataclass(frozen=True)
class DbtRun:
    id: int
    finished_at: datetime


def _account_url(host: str) -> str:
    host = host.rstrip("/")
    return f"{host}{_URL_SUFFIX}"


def _is_deleted(job: dict) -> bool:
    return job["state"] == _DELETED_JOB_STATE


class DbtClient:
    """
    Connect to dbt-cloud Administrative API and downloads manifest.
    https://docs.getdbt.com/docs/dbt-cloud-apis/admin-cloud-api
    """

    def __init__(self, credentials: DbtCredentials):
        self._credentials = credentials
        self._account_url = _account_url(self._credentials.host)
        self._session = requests.Session()
        self._account_id: str = self._infer_account_id()

    def _headers(self, content_type: ContentType) -> dict:
        return {
            "Accept": content_type.value,
            "Authorization": "Token " + self._credentials.token,
        }

    def _call(
        self,
        url: str,
        params: dict | None = None,
        content_type: ContentType = ContentType.JSON,
        ignore_not_found: bool = False,
    ) -> dict:
        headers = self._headers(content_type)
        response = self._session.get(
            url=url,
            headers=headers,
            params=params,
        )

        if ignore_not_found and response.status_code == 404:
            logger.info(f"No results found at {url} (params: {params})")
            return {}

        try:
            result = response.json()
        except:
            context = f"{url}, status {response.status_code}"
            raise ValueError(f"Couldn't extract data from {context}")
        else:
            if content_type == ContentType.JSON:
                return result[_DATA_KEY]
            return result

    def _infer_account_id(self) -> str:
        result = self._call(url=self._account_url)
        return str(result[0]["id"])

    def list_job_identifiers(self) -> set[int]:
        """
        Return the IDs of all non-deleted jobs for this account
        https://docs.getdbt.com/dbt-cloud/api-v2-legacy#tag/Jobs/operation/listJobsForAccount
        """
        url = add_path(self._account_url, self._account_id, "jobs", "/")
        jobs = self._call(url)
        return {job["id"] for job in jobs if not _is_deleted(job)}

    def last_run(
        self,
        job_id: int | None = None,
        finished_at_range: tuple[datetime, datetime] | None = None,
    ) -> DbtRun | None:
        """
        Extract the last successful run id, optionally filtered on a given datetime range
        https://docs.getdbt.com/dbt-cloud/api-v2#tag/Runs/operation/listRunsForAccount
        """
        url = add_path(self._account_url, self._account_id, "runs", "/")

        params = {
            "job_definition_id": job_id or self._credentials.job_id,
            "order_by": "-finished_at",
            "status": _SUCCESSFUL_RUN_STATUS,
            "limit": 1,
        }

        if finished_at_range:
            # https://github.com/dbt-labs/dbt-cloud-openapi-spec/issues/33
            params["finished_at__range"] = json.dumps(
                [d.isoformat() for d in finished_at_range]
            )

        data = self._call(url, params)
        if not data:
            return None

        if not data[0]:
            raise ValueError("API result is empty")

        run = data[0]
        return DbtRun(id=run["id"], finished_at=parse(run["finished_at"]))

    def _fetch_run_artifact(
        self, run_id: int, artifact: Artifact, ignore_not_found=False
    ) -> dict | None:
        """
        Fetch dbt manifest or run results
        https://docs.getdbt.com/dbt-cloud/api-v2-legacy#tag/Runs/operation/getArtifactsByRunId
        """
        url = add_path(
            self._account_url,
            self._account_id,
            "runs",
            str(run_id),
            "artifacts",
            artifact,
        )
        logger.info(
            f"Extracting {artifact} from run id {run_id} with url {url}"
        )

        # setting text content as a workaround to this issue
        # https://stackoverflow.com/questions/68201659/dbt-cloud-api-to-extract-run-artifacts
        return self._call(
            url,
            content_type=ContentType.TEXT,
            ignore_not_found=ignore_not_found,
        )

    def fetch_manifest(self, run_id: int | None = None) -> dict:
        """
        Fetch the manifest or the given run, or of the latest run for the configured job
        """
        if not run_id:
            run = self.last_run()
            assert run, f"No run found for job {self._credentials.job_id}"
            run_id = run.id
        manifest = self._fetch_run_artifact(run_id, "manifest.json")
        assert manifest, f"No manifest found for run id {run_id}"
        return manifest

    def fetch_run_results(self, run_id: int) -> dict | None:
        """
        Fetch the run results of the given run.
        It seems the API doesn't always find the file, in which case None is returned.
        """
        return self._fetch_run_artifact(
            run_id, "run_results.json", ignore_not_found=True
        )

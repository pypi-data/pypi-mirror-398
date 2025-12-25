import logging

import requests
import tableauserverclient as TSC  # type: ignore

from ....utils import SerializedAsset, deduplicate
from ..assets import TableauAsset
from .rest_fields import REST_FIELDS

logger = logging.getLogger(__name__)

_PULSE_API = "api/-/pulse"

_METRICS_DEFINITION_URL = "{base}/pulse/site/{site}/{definition_id}"


def _pick(
    data: SerializedAsset,
    asset: TableauAsset,
) -> SerializedAsset:
    keys = REST_FIELDS[asset]
    return [{key: row[key] for key in keys} for row in data]


class TableauClientRestApi:
    """
    Extract Tableau Assets using REST API
    https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref.htm
    """

    def __init__(
        self,
        server: TSC.Server,
    ):
        self._server = server

    @property
    def timeout_sec(self) -> int:
        return self._server.http_options["timeout"]

    @property
    def headers(self) -> dict[str, str]:
        return {"x-tableau-auth": self._server.auth_token}

    def _get_site_name(self) -> str:
        site_id = self._server.site_id
        site = self._server.sites.get_by_id(site_id)
        return site.content_url

    def _get(
        self,
        url: str,
        page_token: str | None = None,
    ) -> dict:
        if page_token:
            url += f"?page_token={page_token}"

        logger.debug(f"Calling REST API: {url}")
        response = requests.get(
            url,
            headers=self.headers,
            timeout=self.timeout_sec,
        )
        response.raise_for_status()
        return response.json()

    def _call(
        self,
        path: str,
        target: str,
    ) -> SerializedAsset:
        base = self._server.server_address.strip("/")
        url = f"{base}/{path}/{target}"

        next_page_token = None
        data = []

        while True:
            response = self._get(url, next_page_token)
            data += response[target]
            next_page_token = response.get("next_page_token")
            if not next_page_token:
                break

        return data

    def _compute_metric_url(self, data: SerializedAsset) -> None:
        site = self._get_site_name()
        base_url = self._server.server_address.strip("/")
        for row in data:
            row["metadata"]["url"] = _METRICS_DEFINITION_URL.format(
                base=base_url,
                site=site,
                definition_id=row["metadata"]["id"],
            )

    def _fetch_metrics(self, definitions: SerializedAsset) -> SerializedAsset:
        metrics = []
        for definition in definitions:
            definition_id = definition["metadata"]["id"]
            path = f"{_PULSE_API}/definitions/{definition_id}"
            metrics += self._call(path=path, target="metrics")

        # for some reason, the REST API sometimes send the same metric twice
        return deduplicate("id", metrics)

    def fetch(
        self,
        asset: TableauAsset,
    ) -> SerializedAsset:
        if asset == TableauAsset.SUBSCRIPTION:
            # https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_pulse.htm#PulseSubscriptionService_ListSubscriptions
            data = self._call(path=_PULSE_API, target="subscriptions")

        elif asset == TableauAsset.METRIC_DEFINITION:
            # https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_pulse.htm#MetricQueryService_ListDefinitions
            data = self._call(path=_PULSE_API, target="definitions")
            self._compute_metric_url(data)

        elif asset == TableauAsset.METRIC:
            # https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_pulse.htm#MetricQueryService_ListMetrics
            definitions = self._call(path=_PULSE_API, target="definitions")
            data = self._fetch_metrics(definitions)
        else:
            raise AssertionError(f"Unsupported asset {asset} for REST API")

        return _pick(data, asset)

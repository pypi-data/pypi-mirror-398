import logging
from collections.abc import Iterable, Iterator
from datetime import date

from ..assets import PowerBiAsset
from .credentials import PowerbiCredentials
from .graph_api_client import MicrosoftGraphPIClient
from .powerbi_api_client import PowerBIAPIClient

logger = logging.getLogger(__name__)


class PowerbiClient:
    def __init__(
        self,
        credentials: PowerbiCredentials,
    ):
        self.power_bi_client = PowerBIAPIClient(credentials)
        self.graph_api_client = MicrosoftGraphPIClient(credentials)

    def test_connection(self) -> None:
        """Use credentials & verify requesting the API doesn't raise an error"""
        self.power_bi_client._auth.refresh_token()

    def fetch_group_members(
        self,
        group_ids: Iterable[str] | None = None,
    ) -> Iterator[dict]:
        """
        Returns the list of users that are members of the given groups.
        This may contain duplicates.
        """
        if group_ids is None:
            raise ValueError("Missing group IDs to extract users")

        yield from self.graph_api_client.users_in_groups(group_ids)

    def fetch(
        self,
        asset: PowerBiAsset,
        *,
        day: date | None = None,
    ) -> Iterator[dict]:
        """
        Given a PowerBi asset, returns the corresponding data using the
        appropriate client.
        """
        if asset == PowerBiAsset.ACTIVITY_EVENTS:
            yield from self.power_bi_client.activity_events(day=day)

        elif asset == PowerBiAsset.DATASETS:
            yield from self.power_bi_client.datasets()

        elif asset == PowerBiAsset.DASHBOARDS:
            yield from self.power_bi_client.dashboards()

        elif asset == PowerBiAsset.REPORTS:
            yield from self.power_bi_client.reports()

        elif asset == PowerBiAsset.METADATA:
            yield from self.power_bi_client.metadata()

        else:
            raise ValueError(f"This asset {asset} is unknown")

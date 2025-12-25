from dataclasses import dataclass, field

_AUTH_URL = (
    "grant_type=client_credentials&scope=data%20dashboard%20audit%20user"
)
_DOMO_PUBLIC_URL = "https://api.domo.com"
_MAX_URL_LENGTH = 2048


class URLTooLongException(Exception):
    """Custom error handling if the URL is too big"""

    def __init__(self, url: str, max_size: int):
        message = f"The URL is too long ({len(url)} > {max_size}) : {url}"
        super().__init__(message)


@dataclass
class Endpoint:
    """Contains endpoint URL and whether the API targeted is the private one"""

    base_url: str
    is_private: bool = False
    params: dict = field(default_factory=dict)

    def url(self, asset_id: str | None = None):
        return f"{self.base_url}/{asset_id}" if asset_id else self.base_url


class EndpointFactory:
    """List of all Endpoints used for DOMO"""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @property
    def authentication(self) -> Endpoint:
        return Endpoint(f"{_DOMO_PUBLIC_URL}/oauth/token?{_AUTH_URL}")

    @property
    def datasets(self) -> Endpoint:
        return Endpoint(f"{_DOMO_PUBLIC_URL}/v1/datasets")

    @property
    def pages(self) -> Endpoint:
        return Endpoint(f"{_DOMO_PUBLIC_URL}/v1/pages")

    @property
    def users(self) -> Endpoint:
        return Endpoint(f"{_DOMO_PUBLIC_URL}/v1/users")

    @property
    def dataflows(self) -> Endpoint:
        return Endpoint(
            base_url=f"{self.base_url}/api/dataprocessing/v1/dataflows",
            is_private=True,
        )

    def audit(self, start: int, end: int) -> Endpoint:
        """
        start and end are timestamps since epoch in milliseconds
        See [documentation](https://developer.domo.com/portal/a4e18ca6a0c0b-retrieve-activity-log-entries)
        """
        return Endpoint(
            base_url=f"{_DOMO_PUBLIC_URL}/v1/audit",
            params={"start": start, "end": end},
        )

    def lineage(self, dataflow_id: str) -> Endpoint:
        return Endpoint(
            base_url=f"{self.base_url}/api/data/v1/lineage/DATAFLOW/{dataflow_id}",
            is_private=True,
        )

    def table_lineage(self, dataset_id: str, cloud_id: str) -> Endpoint:
        return Endpoint(
            base_url=f"{self.base_url}/api/query/v1/byos/accounts/{cloud_id}/datasets/{dataset_id}/mapping",
            is_private=True,
        )

    def cards_metadata(self, card_ids: list[int]) -> Endpoint:
        urns = ",".join(map(str, card_ids))
        url = f"{self.base_url}/api/content/v1/cards?urns={urns}&parts=datasources"

        if len(url) > _MAX_URL_LENGTH:
            raise URLTooLongException(url, _MAX_URL_LENGTH)

        return Endpoint(base_url=url, is_private=True)

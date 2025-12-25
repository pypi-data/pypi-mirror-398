from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from requests.auth import HTTPBasicAuth

DOMO_ENV_PREFIX = "CASTOR_DOMO_"


class DomoCredentials(BaseSettings):
    """Class to handle Domo rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=DOMO_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    api_token: str = Field(repr=False)
    base_url: str
    client_id: str
    cloud_id: str | None = Field(validation_alias="CLOUD_ID", default=None)
    developer_token: str = Field(repr=False)

    @property
    def authentication(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.client_id, self.api_token)

    @property
    def private_headers(self) -> dict[str, str]:
        return {"X-DOMO-Developer-Token": self.developer_token}

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

SODA_ENV_PREFIX = "CASTOR_SODA_"

_CLOUD_API = "https://cloud.soda.io/api/v1/"


class SodaCredentials(BaseSettings):
    """Class to handle Soda rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=SODA_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    api_key: str = Field(repr=False)
    secret: str = Field(repr=False)
    host: str = Field(default=_CLOUD_API)

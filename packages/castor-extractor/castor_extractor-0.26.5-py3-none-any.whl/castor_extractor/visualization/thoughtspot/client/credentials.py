from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

THOUGHTSPOT_ENV_PREFIX = "CASTOR_THOUGHTSPOT_"


class ThoughtspotCredentials(BaseSettings):
    """Class to handle Thoughtspot rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=THOUGHTSPOT_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    username: str
    password: str = Field(repr=False)
    base_url: str

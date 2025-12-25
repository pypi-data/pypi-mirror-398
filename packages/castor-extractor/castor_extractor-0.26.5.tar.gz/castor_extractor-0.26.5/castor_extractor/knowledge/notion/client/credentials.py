from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CASTOR_ENV_PREFIX = "CASTOR_NOTION_"


class NotionCredentials(BaseSettings):
    """Class to handle Notion rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=CASTOR_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    token: str = Field(repr=False)

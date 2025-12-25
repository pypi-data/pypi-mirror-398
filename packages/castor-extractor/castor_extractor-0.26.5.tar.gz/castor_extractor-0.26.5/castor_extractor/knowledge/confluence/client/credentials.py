from pydantic_settings import BaseSettings, SettingsConfigDict

CASTOR_ENV_PREFIX = "CASTOR_CONFLUENCE_"


class ConfluenceCredentials(BaseSettings):
    """Class to handle Confluence rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=CASTOR_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    account_id: str
    base_url: str
    token: str
    username: str

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

METABASE_API_ENV_PREFIX = "CASTOR_METABASE_API_"


class MetabaseApiCredentials(BaseSettings):
    """Metabase's credentials to connect to Metabase API"""

    model_config = SettingsConfigDict(
        env_prefix=METABASE_API_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    base_url: str
    user: str = Field(validation_alias="CASTOR_METABASE_API_USERNAME")
    password: str = Field(repr=False)

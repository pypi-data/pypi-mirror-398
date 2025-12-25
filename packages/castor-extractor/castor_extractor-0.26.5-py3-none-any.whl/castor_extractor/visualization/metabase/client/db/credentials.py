from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

METABASE_DB_ENV_PREFIX = "CASTOR_METABASE_DB_"


class MetabaseDbCredentials(BaseSettings):
    """Metabase's credentials to connect to Metabase DB"""

    model_config = SettingsConfigDict(
        env_prefix=METABASE_DB_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    host: str
    port: str
    database: str
    schema_: str = Field(
        validation_alias=AliasChoices(
            f"{METABASE_DB_ENV_PREFIX}SCHEMA", "schema"
        )
    )
    user: str = Field(validation_alias=f"{METABASE_DB_ENV_PREFIX}USERNAME")
    password: str = Field(repr=False)

    encryption_secret_key: str | None = Field(repr=False, default=None)
    require_ssl: bool | None = Field(
        validation_alias=f"{METABASE_DB_ENV_PREFIX}REQUIRE_SSL_KEY"
    )

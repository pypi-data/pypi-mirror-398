from dataclasses import field

from pydantic_settings import BaseSettings, SettingsConfigDict

DATABRICKS_ENV_PREFIX = "CASTOR_DATABRICKS_"


class DatabricksCredentials(BaseSettings):
    """
    Credentials needed by Databricks client
    Requires:
    - host
    - http_path
    - token
    """

    host: str
    http_path: str
    token: str = field(metadata={"sensitive": True})

    model_config = SettingsConfigDict(
        env_prefix=DATABRICKS_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

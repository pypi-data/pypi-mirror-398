from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DBT_CLOUD_URL = "https://cloud.getdbt.com"


class DbtCredentials(BaseSettings):
    """dbt credentials: host has default value"""

    host: str = Field(
        default=DEFAULT_DBT_CLOUD_URL, validation_alias="CASTOR_DBT_HOST"
    )
    job_id: str = Field(..., validation_alias="CASTOR_DBT_JOB_ID")
    token: str = Field(..., validation_alias="CASTOR_DBT_TOKEN")
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

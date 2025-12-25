from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .....utils import validate_baseurl

QLIK_ENV_PREFIX = "CASTOR_QLIK_"


class QlikCredentials(BaseSettings):
    """
    Qlik's credentials to connect to the API
    """

    model_config = SettingsConfigDict(
        env_prefix=QLIK_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    api_key: str = Field(repr=False)
    base_url: str

    @field_validator("base_url", mode="before")
    @classmethod
    def _check_base_url(cls, base_url: str) -> str:
        return validate_baseurl(base_url)

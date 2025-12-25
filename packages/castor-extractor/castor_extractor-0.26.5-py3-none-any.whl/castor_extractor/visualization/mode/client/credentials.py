from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MODE_ENV_PREFIX = "CASTOR_MODE_ANALYTICS_"


class ModeCredentials(BaseSettings):
    """Class holding Mode credentials attributes"""

    model_config = SettingsConfigDict(
        env_prefix=MODE_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    host: str
    secret: str = Field(repr=False)
    token: str
    workspace: str

    @field_validator("host", mode="before")
    @classmethod
    def _check_base_url(cls, host: str) -> str:
        return host.rstrip("/")

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CASTOR_ENV_PREFIX = "CASTOR_COALESCE_"


class CoalesceCredentials(BaseSettings):
    """Class to handle Coalesce rest API permissions"""

    model_config = SettingsConfigDict(
        env_prefix=CASTOR_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    host: str
    token: str = Field(repr=False)

    @property
    def token_payload(self) -> dict[str, str]:
        return {
            "client_secret": self.token,
        }

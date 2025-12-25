from looker_sdk.rtl.api_settings import SettingsConfig
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..constants import DEFAULT_LOOKER_TIMEOUT_SECOND, LOOKER_ENV_PREFIX

KEY_LOOKER_TIMEOUT_SECOND = f"{LOOKER_ENV_PREFIX}TIMEOUT_SECOND"


class LookerCredentials(BaseSettings):
    """ValueObject for the credentials"""

    model_config = SettingsConfigDict(
        env_prefix=LOOKER_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    base_url: str
    client_id: str
    client_secret: str = Field(repr=False)
    timeout: int = Field(
        validation_alias=KEY_LOOKER_TIMEOUT_SECOND,
        default=DEFAULT_LOOKER_TIMEOUT_SECOND,
    )

    def to_settings_config(self) -> SettingsConfig:
        return SettingsConfig(
            base_url=self.base_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            timeout=str(self.timeout),
        )

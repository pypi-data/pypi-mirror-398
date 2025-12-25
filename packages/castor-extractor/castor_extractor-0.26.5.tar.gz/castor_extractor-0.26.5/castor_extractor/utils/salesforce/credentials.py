from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

CASTOR_ENV_PREFIX = "CASTOR_SALESFORCE_"


class SalesforceCredentials(BaseSettings):
    """
    Class to handle Salesforce rest API permissions
    """

    model_config = SettingsConfigDict(
        env_prefix=CASTOR_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    base_url: str
    client_id: str
    client_secret: str = Field(repr=False)
    password: str = Field(repr=False)
    security_token: str = Field(repr=False)
    username: str

    @property
    def password_token(self) -> str:
        """Generates the password for authentication"""
        return self.password + self.security_token

    def token_request_payload(self) -> dict[str, str]:
        """
        Params to post to the API in order to retrieve the authentication token
        """
        return {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password_token,
        }

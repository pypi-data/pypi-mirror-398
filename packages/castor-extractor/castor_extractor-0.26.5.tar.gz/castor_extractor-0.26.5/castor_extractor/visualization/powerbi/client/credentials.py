from typing import Any

from pydantic import BaseModel, Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_POWERBI_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]
DEFAULT_GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]
DEFAULT_SCOPES = DEFAULT_POWERBI_SCOPES + DEFAULT_GRAPH_SCOPES

POWERBI_ENV_PREFIX = "CASTOR_POWERBI_"

CLIENT_APP_BASE = "https://login.microsoftonline.com"
REST_API_BASE_PATH = "https://api.powerbi.com/v1.0/myorg"
GRAPH_API_BASE_PATH = "https://graph.microsoft.com/v1.0"


class PowerbiCertificate(BaseModel):
    """
    Supports all dict credentials formats supported by PowerBI
    https://learn.microsoft.com/en-us/python/api/msal/msal.application.confidentialclientapplication
    """

    client_assertion: str | None = None
    passphrase: str | None = None
    private_key: str | None = None
    private_key_pfx_path: str | None = None
    public_certificate: str | None = None
    thumbprint: str | None = None


class PowerbiCredentials(BaseSettings):
    """
    Class to handle authentication to both the Power BI API and
    the Microsoft Graph API
    """

    model_config = SettingsConfigDict(
        env_prefix=POWERBI_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    client_id: str
    tenant_id: str
    secret: str | None = None
    certificate: PowerbiCertificate | None = None
    api_base: str = REST_API_BASE_PATH
    graph_api_base: str = GRAPH_API_BASE_PATH
    login_url: str = CLIENT_APP_BASE
    scopes: list[str] = Field(default_factory=lambda: DEFAULT_SCOPES)

    @field_validator(
        "api_base",
        "graph_api_base",
        "login_url",
        "scopes",
        mode="before",
    )
    @classmethod
    def set_defaults(cls, v: Any | None, info: ValidationInfo) -> Any:
        """
        Defaults need to be set explicitly due to a side effect of the
        `env_prefix` config.
        """
        if v is not None:
            return v

        defaults: dict[str, Any] = {
            "api_base": REST_API_BASE_PATH,
            "graph_api_base": GRAPH_API_BASE_PATH,
            "login_url": CLIENT_APP_BASE,
            "scopes": DEFAULT_SCOPES,
        }
        assert info.field_name
        return defaults[info.field_name]

    @property
    def powerbi_scopes(self) -> list[str]:
        return [scope for scope in self.scopes if "powerbi" in scope.lower()]

    @property
    def graph_scopes(self) -> list[str]:
        return [scope for scope in self.scopes if "graph" in scope.lower()]

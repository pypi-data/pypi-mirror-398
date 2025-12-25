from typing import Literal

import msal  # type: ignore

from ....utils import BearerAuth
from .constants import Keys
from .credentials import PowerbiCertificate, PowerbiCredentials
from .endpoints import PowerBiEndpointFactory

TScope = Literal["powerbi", "graph"]


def _get_client_credential(
    secret: str | None, certificate: PowerbiCertificate | None
) -> str | dict:
    if secret:
        return secret
    if certificate:
        return certificate.model_dump()

    raise ValueError("Either certificate or secret must be provided.")


class PowerBiBearerAuth(BearerAuth):
    """
    Class to handle authentication to both the Power BI API and
    the Microsoft Graph API.
    The only difference lies in the scopes.
    """

    def __init__(
        self,
        credentials: PowerbiCredentials,
        scope_type: TScope = "powerbi",
    ):
        self.credentials = credentials
        self.scopes = self._pick_scopes(scope_type)

        endpoint_factory = PowerBiEndpointFactory(
            login_url=self.credentials.login_url,
            api_base=self.credentials.api_base,
        )
        authority = endpoint_factory.authority(self.credentials.tenant_id)

        client_credential = _get_client_credential(
            self.credentials.secret, self.credentials.certificate
        )

        self.app = msal.ConfidentialClientApplication(
            client_id=self.credentials.client_id,
            authority=authority,
            client_credential=client_credential,
        )

    def _pick_scopes(self, scope_type: TScope) -> list[str]:
        if scope_type == "powerbi":
            return self.credentials.powerbi_scopes

        if scope_type == "graph":
            return self.credentials.graph_scopes

        raise ValueError("scope_type must be either 'powerbi' or 'graph'")

    def fetch_token(self):
        token = self.app.acquire_token_for_client(scopes=self.scopes)

        if Keys.ACCESS_TOKEN not in token:
            raise ValueError(f"No access token in token response: {token}")

        return token[Keys.ACCESS_TOKEN]

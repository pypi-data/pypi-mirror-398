from dataclasses import field

from pydantic.dataclasses import dataclass


@dataclass
class BigQueryCredentials:
    """Credentials needed by BigQuery client"""

    auth_provider_x509_cert_url: str
    auth_uri: str
    client_email: str
    client_id: str
    client_x509_cert_url: str
    private_key: str = field(metadata={"sensitive": True})
    private_key_id: str
    project_id: str
    token_uri: str
    type: str

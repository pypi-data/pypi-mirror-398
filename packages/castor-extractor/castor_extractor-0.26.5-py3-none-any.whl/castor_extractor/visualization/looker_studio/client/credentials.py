from pydantic import BaseModel, SecretStr, field_serializer

SCOPES_NO_ACTIVITY: tuple[str, ...] = (
    "https://www.googleapis.com/auth/datastudio",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
)

DEFAULT_SCOPES: tuple[str, ...] = (
    *SCOPES_NO_ACTIVITY,
    "https://www.googleapis.com/auth/admin.reports.audit.readonly",
)


class LookerStudioCredentials(BaseModel):
    """
    Looker Studio Credentials match the Service Account credentials JSON
    but with an additional admin_email field.
    """

    admin_email: str
    auth_provider_x509_cert_url: str
    auth_uri: str
    client_email: str
    client_id: str
    client_x509_cert_url: str
    private_key: SecretStr
    private_key_id: str
    project_id: str
    token_uri: str
    type: str

    has_view_activity_logs: bool | None = True
    scopes: tuple | None = DEFAULT_SCOPES

    def model_post_init(self, __context):
        """Set scopes based on has_view_activity_logs after initialization"""
        if self.has_view_activity_logs is False:
            self.scopes = SCOPES_NO_ACTIVITY

    @field_serializer("private_key")
    def dump_secret(self, pk):
        """When using model_dump, show private_key value"""
        return pk.get_secret_value()

"""
This file is a proxy to Looker SDK functions using Castor ApiSettings.
"""

from looker_sdk.rtl import transport
from looker_sdk.rtl.api_settings import ApiSettings, SettingsConfig
from looker_sdk.sdk.api40 import methods as methods40

from .credentials import LookerCredentials


def has_admin_permissions(sdk_: methods40.Looker40SDK) -> bool:
    """Check if any of the current user's permissions include admin rights"""
    current_user_id = sdk_.me().id
    if not current_user_id:
        return False
    current_user_roles = sdk_.user_roles(current_user_id)
    return any(
        "administer" in role.permission_set.permissions
        for role in current_user_roles
        if role.permission_set and role.permission_set.permissions
    )


class CastorApiSettings(ApiSettings):
    """SDK settings with initialisation using a credential object instead of a path to a .ini file"""

    def __init__(
        self, credentials: LookerCredentials, sdk_version: str | None = ""
    ):
        """Configure using a config dict"""
        self.config = credentials.to_settings_config()
        self.verify_ssl = True
        self.base_url = self.config.get("base_url", "")
        self.timeout = credentials.timeout
        self.headers = {"Content-Type": "application/json"}
        self.agent_tag = f"{transport.AGENT_PREFIX}"
        if sdk_version:
            self.agent_tag += f" {sdk_version}"

        super().__init__()

    def read_config(self) -> SettingsConfig:
        """Returns a serialization of the credentials"""
        return self.config

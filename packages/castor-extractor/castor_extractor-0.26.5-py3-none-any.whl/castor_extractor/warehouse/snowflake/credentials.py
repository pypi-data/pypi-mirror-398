from dataclasses import field

from pydantic.dataclasses import dataclass


@dataclass
class SnowflakeCredentials:
    """
    Credentials needed by Snowflake client
    Requires:
    - account / user / password
    Or
    - account / user / private_key
    """

    account: str
    user: str

    insecure_mode: bool | None = field(default=False)
    password: str | None = field(metadata={"sensitive": True}, default=None)
    private_key: str | None = field(metadata={"sensitive": True}, default=None)

    def _check_password_xor_private_key(self):
        if not self.password and not self.private_key:
            raise ValueError("Either password or private key is required")
        if self.password and self.private_key:
            raise ValueError("Can't have both private_key and password")

    def __post_init__(self):
        self._check_password_xor_private_key()

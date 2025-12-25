from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# To specify the default site on Tableau Server, you can use an empty string
# https://tableau.github.io/server-client-python/docs/api-ref#authentication
_DEFAULT_SERVER_SITE_ID = ""

# In Castor APP, site_id is mandatory: users can't let this field empty
# In that case, we encourage users to write "Default" instead
_DEFAULT_SITE_ID_USER_INPUT = "default"


TABLEAU_ENV_PREFIX = "CASTOR_TABLEAU_"


class TableauCredentials(BaseSettings):
    """
    Tableau's credentials to connect to both APIs (REST and GRAPHQL)
    """

    model_config = SettingsConfigDict(
        env_prefix=TABLEAU_ENV_PREFIX,
        extra="ignore",
        populate_by_name=True,
    )

    server_url: str
    site_id: str = ""

    password: str | None = None
    token: str | None = None
    token_name: str | None = None
    user: str | None = None

    @field_validator("site_id", mode="before")
    @classmethod
    def _check_site_id(cls, site_id: str | None) -> str:
        if not site_id or site_id.lower() == _DEFAULT_SITE_ID_USER_INPUT:
            return _DEFAULT_SERVER_SITE_ID
        return site_id

    @model_validator(mode="after")
    def _check_user_xor_pat_login(self) -> "TableauCredentials":
        """
        Checks that credentials are correctly input, it means either:
        - User and password are filled
        - Token and Token name are filled
        """
        user_login = self.password and self.user
        pat_login = self.token_name and self.token
        if not user_login and not pat_login:
            raise ValueError("Either token or user identification is required")
        if user_login and pat_login:
            raise ValueError("Can't have both token and user identification")
        return self

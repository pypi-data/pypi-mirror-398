import json
import logging
from typing import Any, cast

from pydantic import BaseModel, field_validator, model_validator

from ...utils import (
    OUTPUT_DIR,
    from_env,
)
from .client import LookerStudioCredentials
from .constants import APPLICATION_CREDENTIALS, LOOKER_STUDIO_ADMIN_EMAIL

logger = logging.getLogger(__name__)

_BIGQUERY_CREDENTIALS_REQUIRED_ERROR = (
    "BigQuery credentials are required when using --source-queries-only mode"
)
_EMPTY_USERS_FILE_ERROR = "The users file must contain at least one user email"
_LOOKER_STUDIO_CREDENTIALS_REQUIRED_ERROR = "Looker Studio credentials are required unless using the --source-queries-only mode"
_USERS_FILE_NOT_A_LIST_ERROR = "The users file must be a list"
_USER_EMAIL_NOT_STRING_ERROR = "All items in the users list must be strings"


class ExtractionParameters(BaseModel):
    bigquery_credentials: dict | None = None
    db_allowed: set[str] | None = None
    db_blocked: set[str] | None = None
    has_source_queries_only: bool
    has_view_activity_logs: bool
    looker_studio_credentials: LookerStudioCredentials | None = None
    output_directory: str
    user_emails: list[str] | None = None

    @field_validator("db_allowed", "db_blocked", mode="before")
    @classmethod
    def _transform_db_list_to_set(
        cls, db_list: list[str] | None
    ) -> set[str] | None:
        return None if db_list is None else set(db_list)

    @field_validator("user_emails", mode="before")
    @classmethod
    def _validate_user_emails(
        cls, user_emails: list[str] | None
    ) -> list[str] | None:
        """
        Raises an error if the user emails are not in the expected format
        (list of strings), or if the list is empty.
        """
        if user_emails is None:
            return user_emails

        if not isinstance(user_emails, list):
            raise TypeError(_USERS_FILE_NOT_A_LIST_ERROR)

        if len(user_emails) == 0:
            raise ValueError(_EMPTY_USERS_FILE_ERROR)

        if not all(isinstance(email, str) for email in user_emails):
            raise TypeError(_USER_EMAIL_NOT_STRING_ERROR)

        return user_emails

    @model_validator(mode="after")
    def validate_credentials_requirements(self):
        """
        Validates that the right credentials are provided based on the extraction mode.
        """
        if self.has_source_queries_only:
            # Source queries only mode - requires BigQuery credentials
            if self.bigquery_credentials is None:
                raise ValueError(_BIGQUERY_CREDENTIALS_REQUIRED_ERROR)
            return self

        if self.looker_studio_credentials is None:
            raise ValueError(_LOOKER_STUDIO_CREDENTIALS_REQUIRED_ERROR)

        return self


def _load_optional_file(file_path: str | None) -> Any | None:
    """Attempts to load a JSON file from the given path."""
    if not file_path:
        return None

    logger.info(f"Loading file {file_path}")
    with open(file_path) as file:
        return json.load(file)


def _load_credentials_or_none(file_path: str | None) -> dict | None:
    """
    Attempts to load the Service Account credentials from a file or from the
    special GOOGLE_APPLICATION_CREDENTIALS variable, if it was provided.
    """
    path = file_path or from_env(APPLICATION_CREDENTIALS, allow_missing=True)
    credentials = _load_optional_file(path)
    return cast(dict, credentials)


def _credentials_or_none(params: dict) -> LookerStudioCredentials | None:
    """
    Builds the Looker Studio credentials by combining the Service Account
    credentials with the admin email. Returns None if credentials are not available.
    """
    path = params.get("credentials")
    credentials = _load_credentials_or_none(path)
    if not credentials:
        return None

    admin_email = params.get("admin_email") or from_env(
        LOOKER_STUDIO_ADMIN_EMAIL
    )
    credentials["admin_email"] = admin_email
    has_view_activity_logs = not params["skip_view_activity_logs"]
    credentials["has_view_activity_logs"] = has_view_activity_logs
    return LookerStudioCredentials(**credentials)


def _bigquery_credentials_or_none(params: dict) -> dict | None:
    """Extracts optional GCP credentials to access BigQuery"""
    path = params.get("bigquery_credentials")
    return _load_credentials_or_none(path)


def set_extraction_parameters(parsed_args: dict) -> ExtractionParameters:
    """
    Builds the ExtractionParameters from the parsed arguments and/or environment variables.
    """
    credentials = _credentials_or_none(parsed_args)
    bigquery_credentials = _bigquery_credentials_or_none(parsed_args)

    db_allowed = parsed_args.get("db_allowed")
    db_blocked = parsed_args.get("db_blocked")
    output_directory = parsed_args.get("output") or from_env(OUTPUT_DIR)
    has_view_activity_logs = bool(not parsed_args["skip_view_activity_logs"])
    source_queries_only = parsed_args.get("source_queries_only", False)

    users_file_path = parsed_args.get("users_file_path")
    user_emails = _load_optional_file(users_file_path)

    return ExtractionParameters(
        bigquery_credentials=bigquery_credentials,
        db_allowed=db_allowed,
        db_blocked=db_blocked,
        has_view_activity_logs=has_view_activity_logs,
        looker_studio_credentials=credentials,
        output_directory=output_directory,
        has_source_queries_only=source_queries_only,
        user_emails=user_emails,
    )

from unittest.mock import Mock

import pytest

from .client import LookerStudioCredentials
from .parameters import (
    _BIGQUERY_CREDENTIALS_REQUIRED_ERROR,
    _EMPTY_USERS_FILE_ERROR,
    _LOOKER_STUDIO_CREDENTIALS_REQUIRED_ERROR,
    _USER_EMAIL_NOT_STRING_ERROR,
    _USERS_FILE_NOT_A_LIST_ERROR,
    ExtractionParameters,
)


def test_ExtractionParameters__validate_user_emails():
    base_params = {
        "bigquery_credentials": {"dummy": "credentials"},
        "has_source_queries_only": True,
        "has_view_activity_logs": False,
        "looker_studio_credentials": None,
        "output_directory": "tmp",
    }

    with pytest.raises(TypeError, match=_USERS_FILE_NOT_A_LIST_ERROR):
        ExtractionParameters(**base_params, user_emails="test")

    with pytest.raises(TypeError, match=_USERS_FILE_NOT_A_LIST_ERROR):
        ExtractionParameters(
            **base_params, user_emails={"not": "the", "right": "format"}
        )

    with pytest.raises(ValueError, match=_EMPTY_USERS_FILE_ERROR):
        ExtractionParameters(**base_params, user_emails=[])

    # Test non-string items
    with pytest.raises(TypeError, match=_USER_EMAIL_NOT_STRING_ERROR):
        ExtractionParameters(**base_params, user_emails=[1, 2, 3])

    # happy cases
    params = ExtractionParameters(
        **base_params, user_emails=["admin@toto.com", "tata@toto.com"]
    )
    assert params.user_emails == ["admin@toto.com", "tata@toto.com"]

    params = ExtractionParameters(**base_params, user_emails=None)
    assert params.user_emails is None


def test_ExtractionParameters_validate_credentials_requirements():
    base_params = {
        "has_view_activity_logs": False,
        "output_directory": "tmp",
        "user_emails": None,
    }

    # source queries only mode requires BigQuery credentials
    with pytest.raises(ValueError, match=_BIGQUERY_CREDENTIALS_REQUIRED_ERROR):
        ExtractionParameters(**base_params, has_source_queries_only=True)

    # happy path : source queries mode + BigQuery credentials
    ExtractionParameters(
        **base_params,
        has_source_queries_only=True,
        bigquery_credentials={"dummy": "credentials"},
    )

    # "normal" mode requires Looker Studio credentials
    with pytest.raises(
        ValueError,
        match=_LOOKER_STUDIO_CREDENTIALS_REQUIRED_ERROR,
    ):
        ExtractionParameters(
            **base_params,
            has_source_queries_only=False,
            looker_studio_credentials=None,
        )

    # happy path : source queries mode + both credentials
    ExtractionParameters(
        **base_params,
        has_source_queries_only=True,
        bigquery_credentials={"dummy": "credentials"},
        looker_studio_credentials=Mock(spec=LookerStudioCredentials),
    )

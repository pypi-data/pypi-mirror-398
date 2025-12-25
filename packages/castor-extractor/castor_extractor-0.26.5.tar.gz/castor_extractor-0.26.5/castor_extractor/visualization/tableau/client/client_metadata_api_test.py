import json

import pytest
from tableauserverclient.server.endpoint.exceptions import NonXMLResponseError

from .client_metadata_api import (
    _TIMEOUT_MESSAGES,
    _check_errors,
    _deduplicate,
    _format_filter_ids,
    _is_relationship_service_war_exception,
)
from .errors import TableauApiError, TableauApiTimeout


def test__deduplicate():
    result_pages = iter(
        [
            [
                {"id": 1, "name": "workbook_1"},
                {"id": 2, "name": "workbook_2"},
            ],
            [
                {"id": 1, "name": "workbook_1"},
                {"id": 3, "name": "workbook_3"},
                {"id": 4, "name": "workbook_4"},
            ],
            [
                {"id": 4, "name": "workbook_4"},
                {"id": 5, "name": "workbook_5"},
                {"id": 5, "name": "workbook_5"},
                {"id": 5, "name": "workbook_5"},
            ],
            [
                {"id": 1, "name": "workbook_1"},
                {"id": 3, "name": "workbook_3"},
            ],
        ]
    )
    deduplicated = _deduplicate(result_pages)
    assert len(deduplicated) == 5
    deduplicated_keys = {item["id"] for item in deduplicated}
    assert deduplicated_keys == {1, 2, 3, 4, 5}


def _timeout_error():
    return {"message": _TIMEOUT_MESSAGES[0]}


def _critical_error():
    return {
        "message": "critical error",
        "extensions": {"severity": "Error"},
    }


def _unknown_severity_error():
    return {
        "message": "unknown severity error",
        "extensions": {"severity": None},
    }


def _warning():
    return {
        "message": "critical error",
        "extensions": {"severity": "Warning"},
    }


def test__check_errors():
    answer = {"data": []}  # no errors
    assert _check_errors(answer) is None

    # only warnings
    answer = {
        "data": [],
        "errors": [
            _warning(),
            _warning(),
            _warning(),
        ],
    }
    assert _check_errors(answer) is None

    # timeout issues should be prio (because they can be retried)
    answer = {
        "data": [],
        "errors": [
            _warning(),
            _critical_error(),
            _timeout_error(),
            _warning(),
        ],
    }
    with pytest.raises(TableauApiTimeout):
        _check_errors(answer)

    # expect critical error
    answer = {
        "data": [],
        "errors": [
            _warning(),
            _warning(),
            _critical_error(),
        ],
    }
    with pytest.raises(TableauApiError):
        _check_errors(answer)

    # unknown severity is considered as critical
    answer = {
        "data": [],
        "errors": [
            _unknown_severity_error(),
            _warning(),
        ],
    }
    with pytest.raises(TableauApiError):
        _check_errors(answer)


def test__format_filter_ids():
    expected = '{ idWithin: ["foo"] }'
    assert _format_filter_ids(["foo"]) == expected

    expected = '{ idWithin: ["foo", "bar"] }'
    assert _format_filter_ids(["foo", "bar"]) == expected


def _non_xml_error(payload: dict):
    error_bytes = json.dumps(payload).encode("utf-8")
    exception = NonXMLResponseError(error_bytes)
    return exception


def test__is_relationship_service_war_exception():
    # happy path
    payload = {
        "status": 401,
        "path": "/relationship-service-war/graphql",
    }
    exception = _non_xml_error(payload)
    assert _is_relationship_service_war_exception(exception) is True

    # another type of NonXmlError
    payload = {
        "status": 500,
        "path": "internal_error/graphql",
    }
    exception = _non_xml_error(payload)
    assert _is_relationship_service_war_exception(exception) is False

    # empty payload
    payload = {}
    exception = _non_xml_error(payload)
    assert _is_relationship_service_war_exception(exception) is False

    # another type of exception
    exception = ValueError("foo")
    assert _is_relationship_service_war_exception(exception) is False

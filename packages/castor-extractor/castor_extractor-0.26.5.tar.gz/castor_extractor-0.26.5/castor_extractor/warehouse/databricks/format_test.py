from datetime import datetime

from .format import (
    DatabricksFormatter,
    _column_path,
    _column_payload,
    _table_payload,
    _to_datetime_or_none,
)


def test__to_datetime_or_none():
    time_ms = 1707734459947
    expected = datetime(2024, 2, 12, 10, 40, 59, 947000)

    assert _to_datetime_or_none(time_ms) == expected

    time_ms = None
    assert _to_datetime_or_none(time_ms) is None


def test_DatabricksFormatter__primary():
    emails = [
        {"type": "work", "value": "louis@evilcorp.com", "primary": False},
        {"type": "work", "value": "thomas@evilcorp.com", "primary": True},
    ]
    assert DatabricksFormatter._primary(emails) == "thomas@evilcorp.com"

    assert DatabricksFormatter._primary([]) is None


def test__table_payload():
    schema = {"id": "id123"}

    table = {
        "name": "baz",
        "catalog_name": "foo",
        "schema_name": "bar",
        "table_type": "MANAGED",
        "owner": "pot@ato.com",
        "table_id": "732pot5e-8ato-4c27-b701-9fa51febc192",
    }
    host = "https://some.cloud.databricks.net/"
    workspace_id = "123456"

    tags = {
        "foo.bar.baz": ["riri", "fifi"],
        "dummy.path": ["loulou"],
    }

    payload = _table_payload(schema, table, host, workspace_id, tags)

    expected = {
        "description": None,
        "id": "732pot5e-8ato-4c27-b701-9fa51febc192",
        "owner_email": "pot@ato.com",
        "schema_id": "id123",
        "table_name": "baz",
        "tags": ["riri", "fifi"],
        "type": "MANAGED",
        "url": "https://some.cloud.databricks.net/explore/data/foo/bar/baz?o=123456",
    }
    assert payload == expected


def test__column_payload():
    table = {
        "catalog_name": "foo",
        "name": "baz",
        "owner": "pot@ato.com",
        "schema_name": "bar",
        "table_id": "732pot5e-8ato-4c27-b701-9fa51febc192",
        "table_type": "MANAGED",
    }
    column = {
        "comment": "some description",
        "name": "Uid",
        "nullable": True,
        "position": 0,
        "type_json": '{"name":"Uid","type":"string","nullable":true,"metadata":{}}',
        "type_name": "STRING",
        "type_precision": 0,
        "type_scale": 0,
        "type_text": "string",
    }
    tags = {
        "foo.bar.baz.Uid": ["riri", "fifi"],
        "dummy.path": ["loulou"],
    }
    payload = _column_payload(table, column, tags)

    expected = {
        "column_name": "Uid",
        "data_type": "STRING",
        "description": "some description",
        "id": "`732pot5e-8ato-4c27-b701-9fa51febc192`.`Uid`",
        "ordinal_position": 0,
        "table_id": "732pot5e-8ato-4c27-b701-9fa51febc192",
        "tags": ["riri", "fifi"],
    }
    assert payload == expected

    # case where there are spaces in the name
    column["name"] = "column name with spaces"
    payload = _column_payload(table, column, tags)
    expected_id = (
        "`732pot5e-8ato-4c27-b701-9fa51febc192`.`column name with spaces`"
    )
    assert payload["id"] == expected_id


def test__column_path():
    table = {
        "catalog_name": "Jo",
        "schema_name": "William",
        "name": "Jack",
    }
    column = {
        "name": "Averell",
    }

    expected = "Jo.William.Jack.Averell"
    assert _column_path(table=table, column=column) == expected

from .format import (
    _HAS_DUPLICATE_KEY,
    SalesforceFormatter,
    _detect_duplicate_labels,
    _field_description,
    _name,
    _remove_duplicates,
)


def _tables_sobjects() -> tuple[dict[str, str], ...]:
    """Returns 4 sobjects with 2 sharing the same label"""
    a = {"Label": "a", "QualifiedApiName": "a_one"}
    b = {"Label": "b", "QualifiedApiName": "b"}
    c = {"Label": "c", "QualifiedApiName": "c_unique_so_doesnt_matter"}
    a_prime = {"Label": "a", "QualifiedApiName": "a_two"}
    b_exact_duplicate = {"Label": "b", "QualifiedApiName": "b"}
    return a, b, c, a_prime, b_exact_duplicate


def _columns_sobjects() -> dict[str, list[dict]]:
    a = {"Label": "First Name", "QualifiedApiName": "owner_name"}
    b = {"Label": "First Name", "QualifiedApiName": "editor_name"}
    c = {"Label": "Foo Bar", "QualifiedApiName": "foo_bar"}
    return {
        "table_1": [a, b],
        "table_2": [c],
    }


def test__field_description():
    field = {}
    assert _field_description(field) == ""

    definition = {}
    field = {"FieldDefinition": definition}
    assert _field_description(field) == ""

    definition.update({"Description": "foo"})
    assert "foo" in _field_description(field)

    field.update({"InlineHelpText": "bar"})
    assert "bar" in _field_description(field)

    definition.update({"ComplianceGroup": "bim"})
    assert "bim" in _field_description(field)

    definition.update({"SecurityClassification": "bam"})
    description = _field_description(field)

    assert "bam" in description
    expected = (
        "- Description: foo\n"
        "- Help Text: bar\n"
        "- Compliance Categorization: bim\n"
        "- Data Sensitivity Level: bam"
    )
    assert description == expected


def test__name():
    unique_sobject = {
        "Label": "First Name",
        "QualifiedApiName": "first_name",
        _HAS_DUPLICATE_KEY: False,
    }
    assert _name(unique_sobject) == "First Name"

    duplicate_sobject = {
        "Label": "First Name",
        "QualifiedApiName": "first_name",
        _HAS_DUPLICATE_KEY: True,
    }
    assert _name(duplicate_sobject) == "First Name (first_name)"

    empty_label_sobject = {
        "Label": "",
        "QualifiedApiName": "empty_label",
        _HAS_DUPLICATE_KEY: False,
    }
    assert _name(empty_label_sobject) == "empty_label"


def test__detect_duplicate_labels():
    objects = [
        {"Label": "Foo"},
        {"Label": "Bar"},
        {"Label": "Foo"},
    ]

    objects = _detect_duplicate_labels(objects)
    assert objects == [
        {"Label": "Foo", _HAS_DUPLICATE_KEY: True},
        {"Label": "Bar", _HAS_DUPLICATE_KEY: False},
        {"Label": "Foo", _HAS_DUPLICATE_KEY: True},
    ]


def test__remove_duplicates():
    objects = [
        {"QualifiedApiName": "Foo"},
        {"QualifiedApiName": "Bar"},
        {"QualifiedApiName": "Foo"},
    ]

    objects = _remove_duplicates(objects)
    assert len(objects) == 2
    names = {sobject["QualifiedApiName"] for sobject in objects}
    assert names == {"Foo", "Bar"}


def test_salesforce_formatter_tables():
    sobjects = [*_tables_sobjects()]
    tables = [t for t in SalesforceFormatter.tables(sobjects)]
    expected_names = {"a (a_one)", "a (a_two)", "b", "c"}
    payload_names = {t["table_name"] for t in tables}
    assert len(tables) == 4  # we only keep one "b"
    assert payload_names == expected_names


def test_salesforce_formatter_columns():
    sobjects = _columns_sobjects()
    columns = SalesforceFormatter.columns(sobjects)
    column_ids = {c["id"] for c in columns}
    expected_column_ids = {
        "table_1.First Name (owner_name)",
        "table_1.First Name (editor_name)",
        "table_2.Foo Bar",
    }
    assert column_ids == expected_column_ids

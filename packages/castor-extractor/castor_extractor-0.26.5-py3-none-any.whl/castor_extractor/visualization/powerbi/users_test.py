from .users import UserDataProcessor

_METADATA = [
    {
        "id": "workspace-one-user-one-group",
        "users": [
            {"graphId": "U1", "displayName": "jean", "principalType": "User"},
            {"graphId": "GR1", "displayName": "GR1", "principalType": "Group"},
        ],
    },
    {
        "id": "workspace-one-user-duplicate-group",
        "users": [
            {"graphId": "U2", "displayName": "michel", "principalType": "User"},
            {"graphId": "GR1", "displayName": "GR1", "principalType": "Group"},
            {"graphId": "?", "displayName": "tata", "principalType": "?"},
        ],
    },
    {"id": "workspace-no-users-field"},
    {"id": "workspace-empty-users-field", "users": []},
]

_GR1_MEMBERS = [
    {"id": "U3", "displayName": "jacques", "mail": "jacques@catylog.com"},
    {"id": "U1", "displayName": "toto", "mail": ""},  # duplicate
]


def test_parse_metadata_and_combine_users():
    processor = UserDataProcessor()
    processor.parse_metadata(_METADATA)

    assert {u["graphId"] for u in processor.users} == {"U1", "U2"}

    combined_users = processor.combine_users(_GR1_MEMBERS)
    assert {u["graphId"] for u in combined_users} == {"U1", "U2", "U3"}


def test__normalize_group_member():
    processor = UserDataProcessor()
    member = _GR1_MEMBERS[0]
    expected_user = {
        "graphId": "U3",
        "displayName": "jacques",
        "emailAddress": "jacques@catylog.com",
    }
    assert processor._normalize_group_member(member) == expected_user

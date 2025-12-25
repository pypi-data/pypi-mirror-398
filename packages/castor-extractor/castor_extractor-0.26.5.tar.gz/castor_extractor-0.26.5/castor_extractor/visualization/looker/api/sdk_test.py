from collections import namedtuple
from unittest.mock import patch

from castor_extractor.visualization.looker.api.sdk import (  # type: ignore
    has_admin_permissions,
)
from looker_sdk.sdk.api40 import methods as methods40  # type: ignore


def get_looker40sdk():
    sdk_attr = {
        "auth": "value_account",
        "deserialize": "value_user",
        "serialize": "value_password",
        "transport": "value_password",
        "api_version": "value_password",
    }
    return methods40.Looker40SDK(**sdk_attr)


MockUser = namedtuple("MockUser", ["id"])
MockRole = namedtuple("MockRole", ["permission_set"])
MockPermissionSet = namedtuple("MockPermissionSet", ["permissions"])


@patch("castor_extractor.visualization.looker.api.sdk.methods40.Looker40SDK")
def test_has_admin_permissions(mock_sdk):
    # unknown user
    mock_sdk.return_value.me.return_value = MockUser(id=None)
    sdk = get_looker40sdk()
    assert not has_admin_permissions(sdk)

    # set a user
    mock_sdk.return_value.me.return_value = MockUser(id="1")

    # user without roles
    mock_sdk.return_value.user_roles.return_value = []
    assert not has_admin_permissions(sdk)

    # user with multiple roles, but no "administer" permission
    mock_sdk.return_value.user_roles.return_value = [
        MockRole(MockPermissionSet(["access_data", "create_custom_fields"])),
        MockRole(MockPermissionSet(["explore"])),
    ]
    assert not has_admin_permissions(sdk)

    # user with "administer" permission
    mock_sdk.return_value.user_roles.return_value = [
        MockRole(MockPermissionSet(["access_data", "create_custom_fields"])),
        MockRole(MockPermissionSet(["explore", "administer"])),
    ]
    assert has_admin_permissions(sdk)

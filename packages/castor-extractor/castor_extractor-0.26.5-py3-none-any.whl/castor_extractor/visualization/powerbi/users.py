import logging
from collections.abc import Iterator
from itertools import chain

from .client import PowerbiClient

logger = logging.getLogger(__name__)

_TYPE_USER = "User"
_TYPE_GROUP = "Group"


class UserDataProcessor:
    def __init__(self):
        self.users: list[dict] = []
        self.group_ids: set[str] = set()

    def parse_metadata(self, metadata: list[dict]) -> None:
        """
        Parses a list of individual users and a set of group IDs from
        the metadata. The list of users may contain duplicates.
        """
        self.users = []
        self.group_ids = set()

        for workspace in metadata:
            for user in workspace.get("users") or []:
                if user["principalType"] == _TYPE_USER:
                    self.users.append(user)

                elif user["principalType"] == _TYPE_GROUP:
                    self.group_ids.add(user["graphId"])

    @staticmethod
    def _normalize_group_member(group_member: dict) -> dict:
        """Normalizes a group member to match the Power BI user format."""
        return {
            "graphId": group_member["id"],
            "emailAddress": group_member["mail"],
            "displayName": group_member["displayName"],
        }

    def combine_users(self, group_members: list[dict]) -> Iterator[dict]:
        """
        Merges the given group members with the list of individual users found
        in the metadata, removing duplicates.
        """
        seen_users = set()
        normalized_group_members = map(
            self._normalize_group_member, group_members
        )

        for user in chain(self.users, normalized_group_members):
            id_ = user["graphId"]
            if id_ in seen_users:
                continue

            seen_users.add(id_)
            yield user


def consolidate_powerbi_users(
    client: PowerbiClient, metadata: list[dict]
) -> Iterator[dict]:
    """
    Extracts Power BI users as follows:
    - Metadata contains user information (individuals and groups)
    - Groups are expanded into its individual members
    - All users are consolidated into a single file

    If the group expansion fails due to a lack of permissions, it will raise
    a custom MicrosoftGraphAccessForbidden Exception.
    """
    user_processor = UserDataProcessor()
    user_processor.parse_metadata(metadata)

    logger.info("Extracting group members from Microsoft Graph API")
    group_members = list(
        client.fetch_group_members(group_ids=user_processor.group_ids)
    )
    combined_users = user_processor.combine_users(group_members)
    return combined_users

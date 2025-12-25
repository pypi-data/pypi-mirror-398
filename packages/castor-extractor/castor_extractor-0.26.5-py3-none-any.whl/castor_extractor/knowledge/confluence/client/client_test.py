from unittest.mock import MagicMock, patch

from .client import ConfluenceClient


def test_ConfluenceClient_folders():
    """
    Folder 1 -> Page A -> Folder 2 -> Folder 3 -> Folder 4 -> Page B
             -> Page C -> Folder 5 -> Page D

    After extracting the pages, we should have all IDs of folders that are
    immediate parents of pages. We still need to look out for nested folders.
    """
    folder_ids = {"1", "3", "4", "5"}
    mock_responses = {
        "1": {"id": "1", "parentType": None, "parentId": None},
        "2": {"id": "2", "parentType": "page", "parentId": "A"},
        "3": {"id": "3", "parentType": "folder", "parentId": "2"},
        "4": {"id": "4", "parentType": "folder", "parentId": "3"},
        "5": {"id": "5", "parentType": "page", "parentId": "C"},
    }

    def mock_get(endpoint):
        folder_id = endpoint.split("/")[-1]
        return mock_responses[folder_id]

    client = ConfluenceClient(credentials=MagicMock())

    with patch.object(client, "_get", side_effect=mock_get):
        result = list(client.folders(folder_ids))

    assert len(result) == 5
    assert {folder["id"] for folder in result} == set(mock_responses.keys())


def test_ConfluenceClient_filtered_spaces_with_allowlist():
    both_blocked_and_allowed_space_id = "789"
    archived_space_id = "934"
    random_space = "1000"

    spaces = [
        # Both blocked and allowed space. "Allowed" setting takes precedence.
        {
            "id": both_blocked_and_allowed_space_id,
            "type": "global",
            "status": "current",
        },
        {"id": archived_space_id, "type": "global", "status": "archived"},
        {"id": random_space, "type": "global", "status": "current"},
    ]
    # the "allowed" list overrides everything else
    client = ConfluenceClient(
        credentials=MagicMock(),
        include_archived_spaces=True,
        space_ids_allowed={
            both_blocked_and_allowed_space_id,
        },
        space_ids_blocked={
            both_blocked_and_allowed_space_id,
        },
    )

    with (
        patch(
            "source.packages.extractor.castor_extractor.knowledge.confluence.client.client.ConfluenceClient._get"
        ),
        patch(
            "source.packages.extractor.castor_extractor.knowledge.confluence.client.client.fetch_all_pages"
        ) as mock_fetch_all_pages,
    ):
        mock_fetch_all_pages.return_value = spaces

        filtered_spaces = list(client.spaces())

        assert len(filtered_spaces) == 1
        filtered_space_ids = {space["id"] for space in filtered_spaces}
        assert set(filtered_space_ids) == {both_blocked_and_allowed_space_id}


def test_ConfluenceClient_filtered_spaces():
    blocked_id = "42"
    personal_id = "666"
    archived_id = "934"
    random_id = "1000"

    # test the other settings : allow personal spaces & block space "42"
    client = ConfluenceClient(
        credentials=MagicMock(),
        include_archived_spaces=False,
        include_personal_spaces=True,
        space_ids_blocked={blocked_id},
    )

    spaces = [
        # Blocked space, to be skipped
        {"id": blocked_id, "type": "global", "status": "current"},
        # Archived space, to be skipped
        {"id": archived_id, "type": "collaboration", "status": "archived"},
        # Personal space, to be included
        {"id": personal_id, "type": "personal", "status": "current"},
        # Valid space
        {"id": random_id, "type": "knowledge_base", "status": "current"},
    ]

    with (
        patch(
            "source.packages.extractor.castor_extractor.knowledge.confluence.client.client.ConfluenceClient._get"
        ),
        patch(
            "source.packages.extractor.castor_extractor.knowledge.confluence.client.client.fetch_all_pages"
        ) as mock_fetch_all_pages,
    ):
        mock_fetch_all_pages.return_value = spaces

        filtered_spaces = list(client.spaces())

        filtered_space_ids = [space["id"] for space in filtered_spaces]

        # no duplicates
        assert len(filtered_space_ids) == len(set(filtered_space_ids))
        assert set(filtered_space_ids) == {personal_id, random_id}

def pages_to_folder_ids(pages: list[dict]) -> set:
    """Returns all unique folder parents."""
    return {
        page["parentId"] for page in pages if page["parentType"] == "folder"
    }


def pages_to_database_ids(pages: list[dict]) -> set:
    """Returns all unique database parents."""
    return {
        page["parentId"] for page in pages if page["parentType"] == "database"
    }

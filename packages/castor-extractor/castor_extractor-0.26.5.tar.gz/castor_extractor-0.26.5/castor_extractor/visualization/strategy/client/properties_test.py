import pytest

from .properties import level_1_folder_id


def test_level_1_folder_id():
    folders = [
        {"id": "toto", "level": 2},
        {"id": "tata", "level": 1},
        {"id": "tutu", "level": 3},
    ]
    assert level_1_folder_id(folders) == "tata"

    folders = []
    with pytest.raises(ValueError, match="No level 1 folder found"):
        level_1_folder_id(folders)

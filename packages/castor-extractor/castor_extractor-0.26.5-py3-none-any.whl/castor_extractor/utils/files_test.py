from unittest.mock import patch

from .files import explode, search_files


def test_explode():
    checks = {
        "/some/path/file.csv": ("/some/path", "file", "csv"),
        "/file.json": ("/", "file", "json"),
        "/without/extension/file": ("/without/extension", "file", ""),
        "file.txt": ("", "file", "txt"),
        "/tmp/.bashrc": ("/tmp", ".bashrc", ""),  # noqa: S108
    }
    for path, expected in checks.items():
        assert explode(path) == expected


def test_search_files():
    file_list = (
        "foo.csv",
        "bar.csv",
        "unknown.csv",
        "123-foo.csv",
        "foo.txt",
        "bar.json",
        "deprecated-foo.csv",
    )

    with patch("glob.glob") as mocked:
        mocked.return_value = file_list
        directory = "/tmp"  # noqa: S108

        # no filters
        files = search_files(directory)
        assert set(files) == set(file_list)

        # filter extensions
        files = search_files(
            directory,
            filter_extensions={"json", "txt"},
        )
        assert set(files) == {"bar.json", "foo.txt"}

        # endswith + does not contain
        files = search_files(
            directory,
            filter_endswith="foo",
            does_not_contain={"deprecated"},
        )
        assert set(files) == {"foo.csv", "foo.txt", "123-foo.csv"}

        # no results
        files = search_files(
            directory,
            filter_extensions={"json"},
            does_not_contain={"bar"},
        )
        assert not files

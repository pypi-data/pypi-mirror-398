import glob
import os


def explode(path: str) -> tuple[str, str, str]:
    """
    Split a file path into 3 parts:
    - Head (directory)
    - File Name
    - Extension (without dot '.')
    """
    head, tail = os.path.split(path)
    name, extension = os.path.splitext(tail)
    extension = extension.lstrip(".")
    return head, name, extension


def search_files(
    directory: str,
    *,
    filter_endswith: str | None = None,
    filter_extensions: set[str] | None = None,
    does_not_contain: set[str] | None = None,
) -> list[str]:
    """Retrieve files in a directory, matching given criteria"""

    def _does_not_contain(path: str) -> bool:
        if does_not_contain is None:
            return True
        _, name, _ = explode(path)
        return not any([(item in name) for item in does_not_contain])

    def _endswith(path: str) -> bool:
        if filter_endswith is None:
            return True
        _, name, _ = explode(path)
        pattern = filter_endswith.lower()
        return name.endswith(pattern)

    def _extension(path: str) -> bool:
        if filter_extensions is None:
            return True
        _, _, ext = explode(path)
        if not ext:
            return False
        return ext.lower().strip(".") in filter_extensions

    all_files = glob.glob(directory + "/*")

    filtered = filter(_does_not_contain, all_files)
    filtered = filter(_endswith, filtered)
    filtered = filter(_extension, filtered)

    return list(filtered)

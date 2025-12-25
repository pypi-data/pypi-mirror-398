import logging
import os
from collections.abc import Iterator

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSION = (".json", ".csv")


def iter_files(repository_path: str) -> Iterator[str]:
    """
    Given a repository path yield all files in that repository
    Removes file whose extension is not allowed
    """

    for file in os.listdir(repository_path):
        _, ext = os.path.splitext(file)
        if ext not in _ALLOWED_EXTENSION:
            logger.info(f"Forbidden file extension : skipping {file}")
            continue
        file_path = os.path.join(repository_path, file)

        if os.path.isfile(file_path):
            yield file_path


def file_exist(f_path: str) -> bool:
    """
    Check if a file exist
    """
    return os.path.exists(os.path.expanduser(f_path))

import logging
from collections.abc import Iterable, Iterator

from ...utils import (
    OUTPUT_DIR,
    current_timestamp,
    deep_serialize,
    from_env,
    get_output_filename,
    write_json,
    write_summary,
)
from .assets import ConfluenceAsset
from .client import ConfluenceClient, ConfluenceCredentials
from .utils import pages_to_database_ids, pages_to_folder_ids

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: ConfluenceClient,
) -> Iterable[tuple[ConfluenceAsset, list | Iterator | dict]]:
    """Iterate over the extracted data from Confluence"""

    logger.info("Extracting USERS from API")
    users = list(deep_serialize(client.users()))
    yield ConfluenceAsset.USERS, users
    logger.info(f"Extracted {len(users)} users from API")

    logger.info("Extracting PAGES from API")
    pages = list(deep_serialize(client.pages()))
    yield ConfluenceAsset.PAGES, pages
    logger.info(f"Extracted {len(pages)} pages from API")

    folder_ids = pages_to_folder_ids(pages)
    logger.info("Extracting FOLDERS from API")
    folders = list(deep_serialize(client.folders(folder_ids)))
    yield ConfluenceAsset.FOLDERS, folders

    database_ids = pages_to_database_ids(pages)
    logger.info("Extracting DATABASES from API")
    databases = list(deep_serialize(client.databases(database_ids)))
    yield ConfluenceAsset.DATABASES, databases


def extract_all(**kwargs) -> None:
    """
    Extract data from Confluence API
    Store the output files locally under the given output_directory
    """

    output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)

    credentials = ConfluenceCredentials(**kwargs)
    client = ConfluenceClient(
        credentials=credentials,
        include_archived_spaces=kwargs.get("include_archived_spaces") or False,
        include_personal_spaces=kwargs.get("include_personal_spaces") or False,
        space_ids_allowed=kwargs.get("space_ids_allowed"),
        space_ids_blocked=kwargs.get("space_ids_blocked"),
    )

    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), output_directory, ts)
        write_json(filename, data)

    es = current_timestamp()

    write_summary(output_directory, ts, duration_second=es - ts)

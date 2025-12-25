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
from .assets import DomoAsset
from .client import DomoClient, DomoCredentials

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: DomoClient,
) -> Iterable[tuple[DomoAsset, list | Iterator | dict]]:
    """Iterate over the extracted data from Domo"""

    logger.info("Extracting PAGES from API")
    pages = client.fetch(DomoAsset.PAGES)
    yield DomoAsset.PAGES, list(deep_serialize(pages))

    logger.info("Extracting DATASETS from API")
    datasets = list(client.fetch(DomoAsset.DATASETS))
    yield DomoAsset.DATASETS, list(deep_serialize(datasets))

    logger.info("Extracting USERS from API")
    users = client.fetch(DomoAsset.USERS)
    yield DomoAsset.USERS, list(deep_serialize(users))

    logger.info("Extracting AUDIT from API")
    audit = client.fetch(DomoAsset.AUDIT)
    yield DomoAsset.AUDIT, list(deep_serialize(audit))

    logging.info("Extracting DATAFLOWS data from API")
    dataflows = client.fetch(DomoAsset.DATAFLOWS)
    yield DomoAsset.DATAFLOWS, list(deep_serialize(dataflows))


def extract_all(**kwargs) -> None:
    """
    Extract data from Domo API
    Store the output files locally under the given output_directory
    """
    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    credentials = DomoCredentials(**kwargs)
    client = DomoClient(credentials=credentials)

    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), _output_directory, ts)
        write_json(filename, data)

    write_summary(_output_directory, ts, base_url=credentials.base_url)

import logging
from collections.abc import Iterable

from ...utils import (
    OUTPUT_DIR,
    current_timestamp,
    deep_serialize,
    from_env,
    get_output_filename,
    write_json,
    write_summary,
)
from .assets import StrategyAsset
from .client import StrategyClient, StrategyCredentials

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: StrategyClient,
) -> Iterable[tuple[str, list | dict]]:
    """Iterate over the extracted data from Strategy"""

    for asset in StrategyAsset.mandatory:
        logger.info(f"Extracting {asset.value.upper()} from REST API")
        data = client.fetch(asset)
        yield asset.name.lower(), list(deep_serialize(data))


def extract_all(**kwargs) -> None:
    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    credentials = StrategyCredentials(**kwargs)

    client = StrategyClient(credentials=credentials)
    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key, _output_directory, ts)
        write_json(filename, data)

    client.close()
    write_summary(_output_directory, ts)

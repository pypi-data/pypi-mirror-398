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
from ...utils.salesforce import SalesforceCredentials
from .assets import SalesforceReportingAsset
from .client import SalesforceReportingClient

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: SalesforceReportingClient,
) -> Iterable[tuple[str, list | dict]]:
    """Iterate over the extracted data from Salesforce"""

    for asset in SalesforceReportingAsset:
        logger.info(f"Extracting {asset.value.upper()} from REST API")
        data = client.fetch(asset)
        yield asset.name.lower(), deep_serialize(data)


def extract_all(**kwargs) -> None:
    """
    Extract data from Salesforce REST API
    Store the output files locally under the given output_directory
    """
    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    credentials = SalesforceCredentials(**kwargs)

    client = SalesforceReportingClient(credentials=credentials)
    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key, _output_directory, ts)
        write_json(filename, data)

    write_summary(_output_directory, ts)

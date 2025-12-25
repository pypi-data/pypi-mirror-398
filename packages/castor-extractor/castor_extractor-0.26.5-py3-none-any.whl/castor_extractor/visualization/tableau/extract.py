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
from .assets import TableauAsset
from .client import TableauClient, TableauCredentials

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: TableauClient,
) -> Iterable[tuple[TableauAsset, list]]:
    """Iterate over the extracted Data from Tableau"""

    for asset in TableauAsset:
        data = client.fetch(asset)
        yield asset, deep_serialize(data)


def extract_all(**kwargs) -> None:
    """
    Extract Data From tableau and store it locally in files under the
    output_directory
    """
    output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    with_columns = not kwargs.get("skip_columns")
    with_fields = not kwargs.get("skip_fields")
    with_pulse = kwargs.get("with_pulse") or False
    page_size = kwargs.get("page_size")
    ignore_ssl = kwargs.get("ignore_ssl") or False
    timestamp = current_timestamp()

    credentials = TableauCredentials(**kwargs)
    client = TableauClient(
        credentials,
        with_columns=with_columns,
        with_fields=with_fields,
        with_pulse=with_pulse,
        override_page_size=page_size,
        ignore_ssl=ignore_ssl,
    )
    client.login()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.value, output_directory, timestamp)
        write_json(filename, data)

    write_summary(
        output_directory,
        timestamp,
        base_url=client.base_url,
        client_name=client.name,
    )

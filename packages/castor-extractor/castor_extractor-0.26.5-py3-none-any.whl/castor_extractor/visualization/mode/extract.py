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
from .assets import ModeAnalyticsAsset as Asset
from .client import Client, ModeCredentials

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: Client,
) -> Iterable[tuple[Asset, list]]:
    """Iterate over the extracted Data From Mode Analytics"""

    datasources = client.fetch(Asset.DATASOURCE)
    yield Asset.DATASOURCE, deep_serialize(datasources)

    collections = client.fetch(Asset.COLLECTION)
    yield Asset.COLLECTION, deep_serialize(collections)

    reports = client.fetch(Asset.REPORT, additional_data=collections)
    yield Asset.REPORT, deep_serialize(reports)

    queries = client.fetch(Asset.QUERY, additional_data=reports)
    yield Asset.QUERY, deep_serialize(queries)

    members = client.fetch(Asset.MEMBER)
    yield Asset.MEMBER, deep_serialize(members)


def extract_all(**kwargs) -> None:
    """Extract Data From Mode Analytics and store it locally in files under the output_directory"""
    output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    credentials = ModeCredentials(**kwargs)
    client = Client(credentials)

    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), output_directory, ts)
        write_json(filename, data)

    write_summary(
        output_directory,
        ts,
        base_url=client.base_url(),
        client_name=client.name(),
    )

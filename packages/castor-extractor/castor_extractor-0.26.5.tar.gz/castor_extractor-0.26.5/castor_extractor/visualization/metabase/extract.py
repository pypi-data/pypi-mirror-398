import logging
from collections.abc import Iterable
from typing import Union

from ...utils import (
    OUTPUT_DIR,
    current_timestamp,
    deep_serialize,
    from_env,
    get_output_filename,
    write_json,
    write_summary,
)
from .assets import MetabaseAsset
from .client import ApiClient, DbClient

logger = logging.getLogger(__name__)

ClientMetabase = Union[DbClient, ApiClient]


def iterate_all_data(
    client: ClientMetabase,
) -> Iterable[tuple[MetabaseAsset, list]]:
    """Iterate over the extracted Data From metabase"""

    yield MetabaseAsset.USER, deep_serialize(client.fetch(MetabaseAsset.USER))
    yield (
        MetabaseAsset.COLLECTION,
        deep_serialize(
            client.fetch(MetabaseAsset.COLLECTION),
        ),
    )
    yield (
        MetabaseAsset.DATABASE,
        deep_serialize(
            client.fetch(MetabaseAsset.DATABASE),
        ),
    )
    yield MetabaseAsset.TABLE, deep_serialize(client.fetch(MetabaseAsset.TABLE))
    yield MetabaseAsset.CARD, deep_serialize(client.fetch(MetabaseAsset.CARD))
    yield (
        MetabaseAsset.DASHBOARD,
        deep_serialize(
            client.fetch(MetabaseAsset.DASHBOARD),
        ),
    )
    yield (
        MetabaseAsset.DASHBOARD_CARDS,
        deep_serialize(
            client.fetch(MetabaseAsset.DASHBOARD_CARDS),
        ),
    )


def extract_all(client: ClientMetabase, **kwargs) -> None:
    """
    Extract Data From metabase
    Store the output files locally under the given output_directory
    """
    output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), output_directory, ts)
        write_json(filename, data)

    write_summary(
        output_directory,
        ts,
        base_url=client.base_url,
        client_name=client.name(),
    )

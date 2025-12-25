import logging
from collections.abc import Iterable

from ...utils import (
    current_timestamp,
    deep_serialize,
    get_output_filename,
    write_json,
    write_summary,
)
from .assets import LookerStudioAsset
from .client import LookerStudioClient
from .parameters import ExtractionParameters, set_extraction_parameters

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: LookerStudioClient, assets: Iterable[LookerStudioAsset]
) -> Iterable[tuple[LookerStudioAsset, list | dict]]:
    """Extracts Looker Studio data depending on the parameters."""
    for asset in assets:
        logger.info(f"Extracting {asset.name} from API")
        data = list(client.fetch(asset))
        yield asset, deep_serialize(data)
        logger.info(f"Extracted {len(data)} {asset.name} from API")


def _extractable_assets(
    parameters: ExtractionParameters,
) -> list[LookerStudioAsset]:
    """Returns the list of assets to extract based on the parameters."""
    if parameters.has_source_queries_only:
        return [LookerStudioAsset.SOURCE_QUERIES]

    assets = [
        LookerStudioAsset.ASSETS,
        LookerStudioAsset.SOURCE_QUERIES,
    ]
    if parameters.has_view_activity_logs:
        assets.append(LookerStudioAsset.VIEW_ACTIVITY)
    return assets


def extract_all(**kwargs) -> None:
    """
    Extracts data from Looker Studio and stores the output files locally under
    the given output_directory.
    """
    parameters = set_extraction_parameters(kwargs)

    client = LookerStudioClient(
        credentials=parameters.looker_studio_credentials,
        bigquery_credentials=parameters.bigquery_credentials,
        user_emails=parameters.user_emails,
        database_allowed=parameters.db_allowed,
        database_blocked=parameters.db_blocked,
    )
    output_dir = parameters.output_directory
    ts = current_timestamp()

    assets = _extractable_assets(parameters)
    for key, data in iterate_all_data(client, assets):
        filename = get_output_filename(
            name=key.name.lower(), output_directory=output_dir, ts=ts
        )
        write_json(filename, data)

    write_summary(output_dir, ts)

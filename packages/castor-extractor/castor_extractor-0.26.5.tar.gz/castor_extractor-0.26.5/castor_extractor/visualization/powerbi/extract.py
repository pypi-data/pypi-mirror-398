import json
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
from .assets import PowerBiAsset
from .client import PowerbiCertificate, PowerbiClient, PowerbiCredentials
from .client.graph_api_client import MicrosoftGraphAccessForbidden
from .users import consolidate_powerbi_users

logger = logging.getLogger(__name__)


_ASSETS_SUBSET = (
    PowerBiAsset.DATASETS,
    PowerBiAsset.DASHBOARDS,
    PowerBiAsset.REPORTS,
    PowerBiAsset.ACTIVITY_EVENTS,
)


def _load_certificate(
    certificate: str | None,
) -> PowerbiCertificate | None:
    if not certificate:
        return None

    with open(certificate) as file:
        cert = json.load(file)
        return PowerbiCertificate(**cert)


def iterate_all_data(
    client: PowerbiClient,
) -> Iterable[tuple[PowerBiAsset, list | dict]]:
    """
    Extracts Power BI data. Metadata and users require special handling.
    The user extraction is skipped if the user does not have access
    to Microsoft Graph.
    """
    for asset in _ASSETS_SUBSET:
        logger.info(f"Extracting {asset.name} from API")
        data = list(deep_serialize(client.fetch(asset)))
        yield asset, data
        logger.info(f"Extracted {len(data)} {asset.name} from API")

    logger.info(f"Extracting {PowerBiAsset.METADATA} from API")
    metadata = list(client.fetch(PowerBiAsset.METADATA))
    yield PowerBiAsset.METADATA, deep_serialize(metadata)

    try:
        combined_users = consolidate_powerbi_users(client, metadata)
        yield PowerBiAsset.USERS, deep_serialize(list(combined_users))
    except MicrosoftGraphAccessForbidden:
        logger.warning(
            "Could not list group members: "
            "the user does not have permissions to access Microsoft Graph."
        )


def extract_all(**kwargs) -> None:
    """
    Extract data from PowerBI REST API
    Store the output files locally under the given output_directory
    """
    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)
    creds = PowerbiCredentials(
        api_base=kwargs.get("api_base"),
        certificate=_load_certificate(kwargs.get("certificate")),
        client_id=kwargs.get("client_id"),
        graph_api_base=kwargs.get("graph_api_base"),
        login_url=kwargs.get("login_url"),
        scopes=kwargs.get("scopes"),
        secret=kwargs.get("secret"),
        tenant_id=kwargs.get("tenant_id"),
    )

    client = PowerbiClient(creds)
    ts = current_timestamp()
    has_users_file = False

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), _output_directory, ts)
        write_json(filename, data)

        if key == PowerBiAsset.USERS:
            has_users_file = True

    write_summary(
        output_directory=_output_directory,
        ts=ts,
        has_powerbi_group_expansion=has_users_file,
    )

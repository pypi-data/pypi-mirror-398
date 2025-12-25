import logging
from collections.abc import Iterable

from looker_sdk.sdk.api40.models import LookmlModel

from ...logger import add_logging_file_handler, set_stream_handler_to_stdout
from ...utils import (
    SafeMode,
    StreamableList,
    current_timestamp,
    deep_serialize,
    get_output_filename,
    write_json,
    write_summary,
)
from .api import (
    ApiClient,
    ExtractionParameters,
    LookerCredentials,
    lookml_explore_names,
)
from .assets import LookerAsset
from .multithreading import MultithreadingFetcher

logger = logging.getLogger(__name__)


def _extract_explores_by_name(
    lookmls: Iterable[LookmlModel], client: ApiClient
) -> Iterable[dict]:
    explore_names = lookml_explore_names(lookmls)
    explores = client.explores(explore_names)
    for explore in explores:
        yield deep_serialize(explore)  # type: ignore


def _safe_mode(
    extraction_parameters: ExtractionParameters,
) -> SafeMode | None:
    if extraction_parameters.is_safe_mode:
        return None
    add_logging_file_handler(extraction_parameters.output)
    return SafeMode((Exception,), float("inf"))


def _client(
    credentials: LookerCredentials,
    safe_mode: SafeMode | None,
    page_size: int,
) -> ApiClient:
    return ApiClient(
        credentials=credentials, safe_mode=safe_mode, page_size=page_size
    )


def iterate_all_data(
    client: ApiClient,
    search_per_folder: bool,
    thread_pool_size: int,
    log_to_stdout: bool,
) -> Iterable[StreamableList | tuple[LookerAsset, list]]:
    """Iterate over the extracted Data From looker"""

    logger.info("Extracting users from Looker API")
    users = client.users()
    yield LookerAsset.USERS, deep_serialize(users)

    logger.info("Extracting folders from Looker API")
    folders = client.folders()
    folder_ids: set[str] = {folder.id for folder in folders if folder.id}
    yield LookerAsset.FOLDERS, deep_serialize(folders)

    logger.info("Extracting looks from Looker API")
    fetcher = MultithreadingFetcher(
        folder_ids=folder_ids,
        client=client,
        thread_pool_size=thread_pool_size,
        log_to_stdout=log_to_stdout,
    )
    if search_per_folder:
        looks_stream = fetcher.fetch_assets(LookerAsset.LOOKS)
        yield LookerAsset.LOOKS, StreamableList(looks_stream)
    else:
        yield LookerAsset.LOOKS, deep_serialize(client.looks())

    logger.info("Extracting dashboards from Looker API")
    if search_per_folder:
        dashboards_stream = fetcher.fetch_assets(LookerAsset.DASHBOARDS)
        yield LookerAsset.DASHBOARDS, StreamableList(dashboards_stream)
    else:
        dashboards = client.dashboards()
        yield LookerAsset.DASHBOARDS, deep_serialize(dashboards)

    logger.info("Extracting lookml models from Looker API")
    lookmls = client.lookml_models()
    yield LookerAsset.LOOKML_MODELS, deep_serialize(lookmls)

    logger.info("Extracting explores from Looker API")
    explores = _extract_explores_by_name(lookmls, client)
    yield LookerAsset.EXPLORES, StreamableList(explores)
    del lookmls

    logger.info("Extracting connections from Looker API")
    yield LookerAsset.CONNECTIONS, deep_serialize(client.connections())

    logger.info("Extracting projects from Looker API")
    yield LookerAsset.PROJECTS, deep_serialize(client.projects())

    logger.info("Extracting groups hierarchy from Looker API")
    groups_hierarchy = client.groups_hierarchy()
    yield LookerAsset.GROUPS_HIERARCHY, deep_serialize(groups_hierarchy)

    logger.info("Extracting groups roles from Looker API")
    yield LookerAsset.GROUPS_ROLES, deep_serialize(client.groups_roles())

    logger.info("Extracting content views from Looker API")
    yield LookerAsset.CONTENT_VIEWS, deep_serialize(client.content_views())

    logger.info("Extracting users attributes from Looker API")
    users_attributes = client.users_attributes()
    yield LookerAsset.USERS_ATTRIBUTES, deep_serialize(users_attributes)


def extract_all(**kwargs) -> None:
    """
    Extract Data From looker and store it locally in files under the
    output_directory
    """
    extraction_parameters = ExtractionParameters(**kwargs)
    output_directory = extraction_parameters.output

    credentials = LookerCredentials(**kwargs)

    if extraction_parameters.log_to_stdout:
        set_stream_handler_to_stdout()

    safe_mode = _safe_mode(extraction_parameters)
    client = _client(
        credentials=credentials,
        safe_mode=safe_mode,
        page_size=extraction_parameters.page_size,
    )

    ts = current_timestamp()

    data = iterate_all_data(
        client=client,
        search_per_folder=extraction_parameters.search_per_folder,
        thread_pool_size=extraction_parameters.thread_pool_size,
        log_to_stdout=extraction_parameters.log_to_stdout,
    )
    for asset, data in data:
        filename = get_output_filename(asset.value, output_directory, ts)
        write_json(filename, data)

    write_summary(output_directory, ts, base_url=credentials.base_url)

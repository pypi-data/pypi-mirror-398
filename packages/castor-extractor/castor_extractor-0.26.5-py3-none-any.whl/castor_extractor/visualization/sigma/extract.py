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
from .assets import SigmaAsset
from .client import SigmaClient, SigmaCredentials

logger = logging.getLogger(__name__)


def iterate_all_data(
    client: SigmaClient,
) -> Iterable[tuple[SigmaAsset, list | Iterator | dict]]:
    """Iterate over the extracted data from Sigma"""

    logger.info("Extracting DATA MODELS from API")
    datamodels = list(client.fetch(SigmaAsset.DATAMODELS))
    yield SigmaAsset.DATASETS, deep_serialize(datamodels)

    logger.info("Extracting DATAMODEL SOURCES from API")
    datamodel_sources = client.fetch(
        SigmaAsset.DATAMODEL_SOURCES, datamodels=datamodels
    )
    yield SigmaAsset.DATAMODEL_SOURCES, list(deep_serialize(datamodel_sources))

    logger.info("Extracting DATASETS from API")
    datasets = list(client.fetch(SigmaAsset.DATASETS))
    yield SigmaAsset.DATASETS, list(deep_serialize(datasets))

    logger.info("Extracting DATASET SOURCES from API")
    dataset_sources = client.fetch(
        SigmaAsset.DATASET_SOURCES, datasets=datasets
    )
    yield SigmaAsset.DATASET_SOURCES, list(deep_serialize(dataset_sources))

    logger.info("Extracting WORKBOOKS from API")
    workbooks = list(client.fetch(SigmaAsset.WORKBOOKS))
    yield SigmaAsset.WORKBOOKS, list(deep_serialize(workbooks))

    logger.info("Extracting WORKBOOK SOURCES from API")
    workbook_sources = client.fetch(
        SigmaAsset.WORKBOOK_SOURCES, workbooks=workbooks
    )
    yield SigmaAsset.WORKBOOKS, list(deep_serialize(workbook_sources))

    logger.info("Extracting FILES from API")
    files = client.fetch(SigmaAsset.FILES)
    yield SigmaAsset.FILES, list(deep_serialize(files))

    logger.info("Extracting MEMBERS from API")
    members = client.fetch(SigmaAsset.MEMBERS)
    yield SigmaAsset.MEMBERS, list(deep_serialize(members))

    logging.info("Extracting QUERIES data from API")
    queries = client.fetch(SigmaAsset.QUERIES, workbooks=workbooks)
    yield SigmaAsset.QUERIES, list(deep_serialize(queries))

    logging.info("Extracting ELEMENTS data from API")
    elements = list(client.fetch(SigmaAsset.ELEMENTS, workbooks=workbooks))
    yield SigmaAsset.ELEMENTS, list(deep_serialize(elements))


def extract_all(**kwargs) -> None:
    """
    Extract data from Sigma API
    Store the output files locally under the given output_directory
    """

    _output_directory = kwargs.get("output") or from_env(OUTPUT_DIR)

    credentials = SigmaCredentials(**kwargs)
    client = SigmaClient(credentials=credentials)

    ts = current_timestamp()

    for key, data in iterate_all_data(client):
        filename = get_output_filename(key.name.lower(), _output_directory, ts)
        write_json(filename, data)

    write_summary(_output_directory, ts, host=credentials.host)

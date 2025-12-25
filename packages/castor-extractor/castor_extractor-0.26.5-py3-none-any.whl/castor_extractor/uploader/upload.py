#!/usr/bin/env python3
import logging
import ntpath
from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

import requests

from ..utils.retry import retry
from .constant import (
    INGEST_URLS,
    PATH_TEMPLATES,
    RETRY_BASE_MS,
    RETRY_JITTER_MS,
    RETRY_STRATEGY,
    FileType,
)
from .enums import Zone
from .env import get_blob_env
from .settings import UploaderSettings
from .utils import iter_files

logger = logging.getLogger(__name__)

_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectTimeout,
)


def _path_and_url(
    source_id: UUID,
    file_type: FileType,
    file_path: str,
    zone: Zone,
) -> tuple[str, str]:
    now = datetime.utcnow()
    timestamp = int(now.timestamp())
    filename = ntpath.basename(file_path)
    path_template = PATH_TEMPLATES[file_type]
    path = path_template.format(
        timestamp=timestamp,
        source_id=source_id,
        filename=filename,
    )

    url = f"{INGEST_URLS[zone]}/{path}"

    return path, url


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Token {token}",
        "Accept": "text/csv, application/json",
    }


def _upload(
    token: str,
    source_id: UUID,
    file_path: str,
    file_type: FileType,
    zone: Zone | None = Zone.EU,
) -> None:
    """
    Upload the given file to Google Cloud Storage (GCS)
    - Don't call GCS API directly
    - Call the ingestion proxy which handles authorisation and uploading
    """
    if not zone:
        zone = Zone.EU
    path, url = _path_and_url(source_id, file_type, file_path, zone)
    headers = _headers(token)
    timeout, max_retries = get_blob_env()

    with open(file_path, "rb") as file_content:

        @retry(
            exceptions=_EXCEPTIONS,
            max_retries=max_retries,
            base_ms=RETRY_BASE_MS,
            jitter_ms=RETRY_JITTER_MS,
            strategy=RETRY_STRATEGY,
        )
        def _request_post():
            response = requests.post(
                url=url,
                headers=headers,
                files={"file": file_content},
                timeout=timeout,
            )
            response.raise_for_status()

        _request_post()

    logger.info(f"Uploaded {file_path} as {file_type.value} to {path}")


def upload_manifest(
    token: str,
    source_id: UUID,
    zone: Zone | None,
    file_path: str | None = None,
) -> None:
    """
    token: backend public API token
    source_id: id for the source
    file_path: path to the local manifest to upload
    """
    if not file_path:
        raise ValueError("file path is needed to upload a manifest")
    _upload(
        token=token,
        source_id=source_id,
        file_path=file_path,
        file_type=FileType.DBT,
        zone=zone,
    )


def upload(
    token: str,
    source_id: UUID,
    file_type: FileType,
    zone: Zone | None,
    file_path: str | None = None,
    directory_path: str | None = None,
) -> None:
    """
    token: backend public API token
    source_id: id for the source
    file_type: type of file(s) uploaded - see FileType Enum
    file_path: path to the local visualization or warehouse file to upload
    directory_path: path to the local directory containing files to upload
    """
    files: Iterable[str]
    if directory_path:
        files = iter_files(directory_path)
    elif file_path:
        files = [file_path]
    else:
        message = "either file_path or directory_path should be defined"
        raise ValueError(message)

    for file_ in files:
        _upload(
            token=token,
            source_id=source_id,
            file_path=file_,
            file_type=file_type,
            zone=zone,
        )


def upload_any(**kwargs) -> None:
    """
    entrypath to upload either a file or a manifest

    token: backend public API token
    source_id: id for the source
    file_type: type of file(s) uploaded - see FileType Enum
    file_path: path to the local visualization or warehouse file to upload
    directory_path: path to the local directory containing files to upload
    """

    settings = UploaderSettings(**kwargs)
    file_type = settings.file_type

    if file_type == FileType.DBT:
        assert not settings.directory_path
        upload_manifest(
            token=settings.token,
            source_id=settings.source_id,
            file_path=settings.file_path,
            zone=settings.zone,
        )
        return None

    upload(
        token=settings.token,
        source_id=settings.source_id,
        file_type=file_type,
        file_path=settings.file_path,
        directory_path=settings.directory_path,
        zone=settings.zone,
    )

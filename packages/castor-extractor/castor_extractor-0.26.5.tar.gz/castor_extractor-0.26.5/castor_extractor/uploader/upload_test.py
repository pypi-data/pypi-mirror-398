from uuid import UUID

from .constant import INGEST_URLS, FileType
from .enums import Zone
from .upload import _path_and_url


def test__path():
    source_id = UUID("399a8b22-3187-11ec-8d3d-0242ac130003")
    file_type = FileType.VIZ
    file_path = "filename"
    zone = Zone.EU

    path, url = _path_and_url(source_id, file_type, file_path, zone)
    assert path == f"visualization-{source_id}/{file_path}"
    assert url == f"{INGEST_URLS[Zone.EU]}/{path}"

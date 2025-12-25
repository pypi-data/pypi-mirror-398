from ..assets import QlikAsset

APP_EXTERNAL_ID_KEY = "resourceId"
SPACE_EXTERNAL_ID_KEY = "spaceId"

# API settings
REST_API_BASE_PATH = "api/v1/"

# requests retry settings
RETRY_COUNTS = 3
RETRY_STATUSES = (404, 500, 502, 503, 504)
RETRY_BACKOFF_FACTOR = 0.5

_RESPONSE_BASE_EXPECTED_MSG = "Expecting HTTP response to be a {type}"
RESPONSE_DICT_EXPECTED_MSG = _RESPONSE_BASE_EXPECTED_MSG.format(type="dict")
RESPONSE_LIST_EXPECTED_MSG = _RESPONSE_BASE_EXPECTED_MSG.format(type="list")


ASSET_PATHS: dict[QlikAsset, str] = {
    QlikAsset.CONNECTIONS: "data-connections",
    QlikAsset.SPACES: "spaces",
    QlikAsset.USERS: "users",
    QlikAsset.APPS: "items?resourceType=app",
    QlikAsset.LINEAGE: "apps/{app_id}/data/lineage",
}

SCOPED_ASSETS = (QlikAsset.LINEAGE, QlikAsset.MEASURES)

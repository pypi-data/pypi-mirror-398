from enum import Enum

WS_HOST_TEMPLATE = "wss://{hostname}/app/{{app_id}}"

DEFAULT_HANDLE = -1

ACCESS_DENIED_ERROR_CODE = 5
APP_SIZE_EXCEEDED_ERROR_CODE = 1015
PERSISTENCE_READ_FAILED_ERROR_CODE = 9001

MEASURES_SESSION_PARAMS = (
    {
        "qInfo": {
            "qType": "MeasureList",
        },
        "qMeasureListDef": {
            "qType": "measure",
            "qData": {
                "title": "/title",
                "tags": "/tags",
                "measure": "/qMeasure",
            },
        },
    },
)


class JsonRpcMethod(Enum):
    """
    Set of JSON-RPC methods used to retrieve the list of measures
    """

    OPEN_DOC = "OpenDoc"
    CREATE_SESSION_OBJECT = "CreateSessionObject"
    GET_LAYOUT = "GetLayout"
    GET_OBJECTS = "GetObjects"
    GET_OBJECT = "GetObject"

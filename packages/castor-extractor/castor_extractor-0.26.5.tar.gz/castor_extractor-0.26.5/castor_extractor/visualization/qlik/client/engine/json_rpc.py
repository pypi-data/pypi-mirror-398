import logging

from .constants import DEFAULT_HANDLE, JsonRpcMethod
from .error import raise_for_error
from .websocket import WebsocketConnection

logger = logging.getLogger(__name__)


class JsonRpcClient:
    """
    JSON-RPC client connecting to QlikSense through websocket

    doc: https://qlik.dev/apis/json-rpc/qix
    """

    VERSION = "2.0"

    def __init__(self, websocket: WebsocketConnection):
        self.websocket = websocket
        self.call_id = 0

    def _increment_call_id(self):
        self.call_id += 1

    def _format_message(
        self,
        method: JsonRpcMethod,
        handle: int,
        params: list | None | dict | None = None,
    ) -> dict:
        params = params or list()
        message = {
            "jsonrpc": self.VERSION,
            "method": method.value,
            "id": self.call_id,
            "handle": handle,
            "params": params,
        }
        return message

    def send_message(
        self,
        method: JsonRpcMethod,
        handle: int = DEFAULT_HANDLE,
        params: list | None | dict | None = None,
    ) -> dict:
        """Sends JSON-RPC message through websocket and checks no error"""
        self._increment_call_id()
        message = self._format_message(method, handle, params)
        response = self.websocket.call(message=message)
        raise_for_error(message, response)
        return response

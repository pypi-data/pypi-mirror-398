import json
from contextlib import contextmanager
from urllib.parse import urlsplit

import websocket  # type: ignore

from .constants import WS_HOST_TEMPLATE


def _ws_host_from_server_url(server_url: str) -> str:
    """Formats the websocket host from the server url"""
    split = urlsplit(server_url)
    return WS_HOST_TEMPLATE.format(hostname=split.hostname)


class WebsocketConnection:
    """
    A WebsocketConnection is a websocket connection opened for a given Qlik
    <app_id> to call the Qlik Engine Api

    doc: https://qlik.dev/apis/json-rpc/qix
    """

    def __init__(self, server_url: str, api_key: str):
        self.ws = websocket.WebSocket()
        self.origin = server_url
        self.host_template = _ws_host_from_server_url(server_url)
        self.api_key = api_key

        self.session: dict = {}

    def connect(self, app_id: str) -> None:
        """Connects the websocket to a qlik source"""
        auth_header = {"Authorization": "Bearer " + self.api_key}
        app_host = self.host_template.format(app_id=app_id)
        self.ws.connect(app_host, header=auth_header, origin=self.origin)
        self.session = json.loads(self.ws.recv())

    def _send_call(self, call_msg: str):
        self.ws.send(call_msg)
        return self.ws.recv()

    def call(self, message: dict) -> dict:
        """
        Sends a JSON-RPC message through the websocket connection and returns
        the response as dict.
        """
        serialized = json.dumps(message)
        _response = self._send_call(serialized)

        if not _response:
            return {}

        return json.loads(_response)

    def close(self):
        """
        Closes websocket connection.
        """
        self.ws.close()


@contextmanager
def open_websocket(app_id: str, server_url: str, api_key: str):
    """
    Context manager over websocket to connect to a Qlik source and close the
    connection at the end.
    """
    ws = WebsocketConnection(server_url, api_key)
    ws.connect(app_id=app_id)
    try:
        yield ws
    finally:
        ws.close()

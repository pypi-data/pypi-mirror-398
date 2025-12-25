from unittest.mock import patch

from .constants import JsonRpcMethod
from .json_rpc import JsonRpcClient
from .websocket import WebsocketConnection


def test_json_rpc_client__send_message():
    dummy_server_url = "toto.fr"
    dummy_api_key = "IAmNotATrueSecretKey"
    ws = WebsocketConnection(server_url=dummy_server_url, api_key=dummy_api_key)

    client = JsonRpcClient(websocket=ws)
    any_method = JsonRpcMethod.OPEN_DOC

    mock_response = {"data": "all qlik"}
    with patch.object(WebsocketConnection, "call") as mock_call:
        mock_call.return_value = mock_response

        assert client.call_id == 0

        response = client.send_message(any_method)
        assert response == mock_response
        assert client.call_id == 1
        expected = {
            "jsonrpc": "2.0",
            "method": "OpenDoc",
            "id": 1,
            "handle": -1,
            "params": [],
        }
        mock_call.assert_called_with(message=expected)

        client.send_message(any_method, handle=12, params=["toto"])
        assert client.call_id == 2
        expected = {
            "jsonrpc": "2.0",
            "method": "OpenDoc",
            "id": 2,
            "handle": 12,
            "params": ["toto"],
        }
        mock_call.assert_called_with(message=expected)

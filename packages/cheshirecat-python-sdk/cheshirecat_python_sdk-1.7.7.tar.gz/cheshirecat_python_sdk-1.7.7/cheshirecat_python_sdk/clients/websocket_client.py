from urllib.parse import urlencode
from websockets import connect, ClientConnection
from websockets.exceptions import InvalidURI


class WSClient:
    def __init__(
        self,
        host: str,
        port: int | None = None,
        apikey: str | None = None,
        is_wss: bool | None = False,
    ):
        self.host = host
        self.port = port
        self.apikey = apikey
        self.token = None
        self.is_wss = is_wss
        self.ws_client = None

    def set_token(self, token: str) -> "WSClient":
        self.token = token
        return self

    def get_ws_uri(
        self,
        agent_id: str,
        user_id: str,
        chat_id: str | None = None,
    ) -> str:
        query = {"user_id": user_id}

        scheme = "wss" if self.is_wss else "ws"
        path = f"ws/{agent_id}"
        if chat_id:
            path += f"/{chat_id}"

        query_string = urlencode(query)
        port_suffix = f":{self.port}" if self.port else ""

        return f"{scheme}://{self.host}{port_suffix}/{path}?{query_string}"

    async def get_client(self, agent_id: str, user_id: str, chat_id: str | None = None) -> ClientConnection:
        uri = self.get_ws_uri(agent_id, user_id, chat_id)
        if self.ws_client is None:
            try:
                if self.token:
                    headers = {"Authorization": f"Bearer {self.token}"}
                elif self.apikey:
                    headers = {"Authorization": f"Bearer {self.apikey}"}
                else:
                    raise ValueError("You must provide an apikey or a token")

                # Create a WebSocket connection
                websocket = await connect(uri, ping_interval=100000, ping_timeout=100000, additional_headers=headers)
                self.ws_client = websocket
            except InvalidURI as e:
                raise ValueError(f"Invalid WebSocket URI: {uri}") from e

        return self.ws_client

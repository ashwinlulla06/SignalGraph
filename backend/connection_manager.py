from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

class ConnectionManager:
    def __init__(self):
        self._active_connections: list[WebSocket] = []

    async def connect(self, websocket:WebSocket):
        await websocket.accept()

        self._active_connections.append(websocket)

        print(f"Websocket connected. Active connections: {self.connection_count}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)

        print(f"WebSocket disconnected. Active connections: {self.connection_count}")

    async def broadcast(self, ongoing_message:BaseModel):
        message = ongoing_message.model_dump(mode="json")

        for websocket in self._active_connections.copy():
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        return len(self._active_connections)
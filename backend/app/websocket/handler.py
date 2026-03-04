import json
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, Query

from app.services.auth import AuthService


class ConnectionManager:
    def __init__(self):
        self._connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID) -> None:
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: UUID) -> None:
        if user_id in self._connections:
            try:
                self._connections[user_id].remove(websocket)
            except ValueError:
                pass
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: UUID, data: dict) -> None:
        if user_id not in self._connections:
            return
        payload = json.dumps(data)
        dead = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            try:
                self._connections[user_id].remove(ws)
            except ValueError:
                pass
        if user_id in self._connections and not self._connections[user_id]:
            del self._connections[user_id]


connection_manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., alias="token"),
):
    user_id = AuthService.decode_token(token)
    if user_id is None:
        await websocket.close(code=4001)
        return
    await connection_manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(websocket, user_id)

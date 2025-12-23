from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import random

router = APIRouter()

# -------------------------
# Room Manager
# -------------------------
class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, List[tuple[str, WebSocket]]] = {}

    def create_room(self) -> str:
        room_id = str(random.randint(100000, 999999))
        self.rooms[room_id] = []
        print("Room created:", room_id)
        return room_id

    async def join(self, room_id: str, username: str, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(room_id, []).append((username, ws))
        await self.system_message(room_id, f"{username} joined the room")

    def leave(self, room_id: str, username: str, ws: WebSocket):
        self.rooms[room_id] = [
            (u, w) for (u, w) in self.rooms.get(room_id, []) if w != ws
        ]
        if not self.rooms[room_id]:
            del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: str, sender_ws: WebSocket):
        for _, ws in self.rooms.get(room_id, []):
            if ws != sender_ws:
                await ws.send_text(message)

    async def system_message(self, room_id: str, message: str):
        for _, ws in self.rooms.get(room_id, []):
            await ws.send_text(f"__SYSTEM__:{message}")


manager = RoomManager()

# -------------------------
# HTTP: Create Room
# -------------------------
@router.get("/create-room")
def create_room():
    return {"room_id": manager.create_room()}

# -------------------------
# WebSocket: Chat
# -------------------------
@router.websocket("/ws/{room_id}")
async def chat(ws: WebSocket, room_id: str):
    username = ws.query_params.get("username")
    if not username:
        await ws.close()
        return

    try:
        await manager.join(room_id, username, ws)
        while True:
            msg = await ws.receive_text()
            await manager.broadcast(room_id, f"{username}: {msg}", ws)
    except WebSocketDisconnect:
        manager.leave(room_id, username, ws)
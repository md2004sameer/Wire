from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, List
import random

print("🔥 Wire Chat with Username Support Loaded 🔥")

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

@app.get("/")
def landing_page():
    return FileResponse(STATIC_DIR / "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -------------------------
# Room Manager
# -------------------------
class RoomManager:
    def __init__(self):
        # room_id -> list of (username, websocket)
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
        try:
            self.rooms[room_id] = [
                (u, w) for (u, w) in self.rooms.get(room_id, []) if w != ws
            ]
            self.system_message_sync(room_id, f"{username} left the room")

            if not self.rooms[room_id]:
                del self.rooms[room_id]

        except Exception as e:
            print("Leave error:", e)

    async def broadcast(self, room_id: str, message: str, sender_ws: WebSocket):
        for username, ws in self.rooms.get(room_id, []):
            if ws != sender_ws:
                try:
                    await ws.send_text(message)
                except Exception as e:
                    print("Send error:", e)

    async def system_message(self, room_id: str, message: str):
        for _, ws in self.rooms.get(room_id, []):
            try:
                await ws.send_text(f"__SYSTEM__:{message}")
            except:
                pass

    def system_message_sync(self, room_id: str, message: str):
        # used on disconnect (no await allowed)
        for _, ws in self.rooms.get(room_id, []):
            try:
                ws.send_text(f"__SYSTEM__:{message}")
            except:
                pass


manager = RoomManager()

@app.get("/create-room")
def create_room():
    return {"room_id": manager.create_room()}

# -------------------------
# WebSocket with Username
# -------------------------
@app.websocket("/ws/{room_id}")
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

    except Exception as e:
        print("WebSocket error:", e)
        manager.leave(room_id, username, ws)

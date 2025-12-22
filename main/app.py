from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, List
import random

print("🔥 WebSocket Chat App Loaded 🔥")

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# -------------------------
# Pages
# -------------------------
@app.get("/")
def landing_page():
    return FileResponse(STATIC_DIR / "index.html")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -------------------------
# Room Manager
# -------------------------
class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    def create_room(self) -> str:
        room_id = str(random.randint(100000, 999999))
        self.rooms[room_id] = []
        print("Room created:", room_id)
        return room_id

    async def join(self, room_id: str, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(room_id, []).append(ws)
        print(f"User joined room {room_id}")

    def leave(self, room_id: str, ws: WebSocket):
        try:
            self.rooms[room_id].remove(ws)
            if not self.rooms[room_id]:
                del self.rooms[room_id]
            print(f"User left room {room_id}")
        except Exception as e:
            print("Leave error:", e)

    async def broadcast(self, room_id: str, msg: str, sender: WebSocket):
        for ws in self.rooms.get(room_id, []):
            if ws != sender:
                try:
                    await ws.send_text(msg)
                except Exception as e:
                    print("Send error:", e)

manager = RoomManager()

# -------------------------
# Create Room API
# -------------------------
@app.get("/create-room")
def create_room():
    room_id = manager.create_room()
    return {"room_id": room_id}

# -------------------------
# WebSocket Chat
# -------------------------
@app.websocket("/ws/{room_id}")
async def chat(ws: WebSocket, room_id: str):
    try:
        await manager.join(room_id, ws)
        await ws.send_text(f"__SYSTEM__:Connected to room {room_id}")

        while True:
            msg = await ws.receive_text()
            await manager.broadcast(room_id, msg, ws)

    except WebSocketDisconnect:
        manager.leave(room_id, ws)

    except Exception as e:
        print("WebSocket error:", e)
        manager.leave(room_id, ws)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from main.ws_manager import manager  # SAME INSTANCE

router = APIRouter()

@router.websocket("/ws/feed")
async def feed_ws(ws: WebSocket):
    print("🟢 WS CONNECT")
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        print("🔴 WS DISCONNECT")
        manager.disconnect(ws)
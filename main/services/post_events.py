from main.ws_manager import manager  # SAME INSTANCE

async def broadcast_new_post(post: dict):
    print("📢 broadcasting to", len(manager.active), "clients")
    await manager.broadcast({
        "type": "new_post",
        "post": post
    })
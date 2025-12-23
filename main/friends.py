from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel
from typing import List

from main.deps import get_current_user
from main.database import (
    relationships_collection,
    profiles_collection,
    notifications_collection,
)

router = APIRouter(prefix="/friends", tags=["Friends"])


# ======================
# SCHEMA
# ======================

class UsernamePayload(BaseModel):
    username: str


# ======================
# HELPERS
# ======================

def me(user: dict) -> str:
    username = user.get("username")
    if not username:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return username.lower()


# ======================
# FOLLOW / REQUEST
# ======================

@router.post("/follow", status_code=201)
async def follow_user(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    from_username = me(user)
    to_username = payload.username.strip().lower()

    if not to_username:
        raise HTTPException(400, "Username required")

    if from_username == to_username:
        raise HTTPException(400, "Cannot follow yourself")

    target = await profiles_collection.find_one(
        {"username": to_username},
        {"is_private": 1}
    )
    if not target:
        raise HTTPException(404, "User not found")

    status_value = "pending" if target.get("is_private") else "accepted"
    now = datetime.utcnow()

    try:
        await relationships_collection.insert_one({
            "from_username": from_username,
            "to_username": to_username,
            "status": status_value,
            "created_at": now,
            "updated_at": now,
        })
    except Exception:
        raise HTTPException(409, "Request already exists")

    # 🔔 notification
    await notifications_collection.insert_one({
        "to_username": to_username,
        "from_username": from_username,
        "type": "follow_request" if status_value == "pending" else "follow",
        "created_at": now,
        "seen": False,
    })

    return {"status": status_value}


# ======================
# ACCEPT REQUEST
# ======================

@router.post("/accept")
async def accept_request(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    to_username = me(user)
    from_username = payload.username.strip().lower()

    result = await relationships_collection.update_one(
        {
            "from_username": from_username,
            "to_username": to_username,
            "status": "pending",
        },
        {
            "$set": {
                "status": "accepted",
                "updated_at": datetime.utcnow(),
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Request not found")

    # 🔔 notification
    await notifications_collection.insert_one({
        "to_username": from_username,
        "from_username": to_username,
        "type": "follow_accepted",
        "created_at": datetime.utcnow(),
        "seen": False,
    })

    return {"status": "accepted"}


# ======================
# REJECT REQUEST
# ======================

@router.post("/reject")
async def reject_request(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    to_username = me(user)
    from_username = payload.username.strip().lower()

    result = await relationships_collection.delete_one({
        "from_username": from_username,
        "to_username": to_username,
        "status": "pending",
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Request not found")

    return {"status": "rejected"}


# ======================
# UNFOLLOW
# ======================

@router.post("/unfollow")
async def unfollow(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    from_username = me(user)
    to_username = payload.username.strip().lower()

    result = await relationships_collection.delete_one({
        "from_username": from_username,
        "to_username": to_username,
        "status": "accepted",
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Not following")

    return {"status": "unfollowed"}


# ======================
# LIST FOLLOWING
# ======================

@router.get("/following")
async def list_following(user=Depends(get_current_user)):
    username = me(user)

    cursor = relationships_collection.find(
        {"from_username": username, "status": "accepted"},
        {"_id": 0, "to_username": 1}
    )

    users = [d["to_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# ======================
# LIST FOLLOWERS
# ======================

@router.get("/followers")
async def list_followers(user=Depends(get_current_user)):
    username = me(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "accepted"},
        {"_id": 0, "from_username": 1}
    )

    users = [d["from_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# ======================
# RELATIONSHIP STATUS
# ======================

@router.get("/status/{username}")
async def relationship_status(
    username: str,
    user=Depends(get_current_user)
):
    viewer = me(user)
    target = username.strip().lower()

    if viewer == target:
        return {"status": "self"}

    outgoing = await relationships_collection.find_one(
        {"from_username": viewer, "to_username": target}
    )
    if outgoing:
        return {
            "status": "following"
            if outgoing["status"] == "accepted"
            else outgoing["status"]
        }

    incoming = await relationships_collection.find_one(
        {
            "from_username": target,
            "to_username": viewer,
            "status": "pending",
        }
    )
    if incoming:
        return {"status": "incoming_request"}

    return {"status": "none"}


# ======================
# BATCH STATUS (EXPLORE PAGE)
# ======================

@router.post("/status/batch")
async def batch_status(
    usernames: List[str],
    user=Depends(get_current_user)
):
    viewer = me(user)

    targets = [
        u.strip().lower()
        for u in usernames
        if u.strip() and u.strip().lower() != viewer
    ]

    if not targets:
        return {}

    status_map = {}

    cursor = relationships_collection.find({
        "from_username": viewer,
        "to_username": {"$in": targets}
    })

    async for r in cursor:
        status_map[r["to_username"]] = (
            "following" if r["status"] == "accepted" else r["status"]
        )

    cursor = relationships_collection.find({
        "from_username": {"$in": targets},
        "to_username": viewer,
        "status": "pending",
    })

    async for r in cursor:
        status_map.setdefault(r["from_username"], "incoming_request")

    return {u: status_map.get(u, "none") for u in targets}


# ======================
# NOTIFICATIONS (FOLLOW)
# ======================

@router.get("/notifications")
async def friend_notifications(user=Depends(get_current_user)):
    username = me(user)

    cursor = notifications_collection.find(
        {"to_username": username}
    ).sort("created_at", -1)

    return [
        {
            "type": n["type"],
            "from": n["from_username"],
            "created_at": n["created_at"],
            "post_id": n.get("post_id"),
            "seen": n.get("seen", False),
        }
        async for n in cursor
    ]
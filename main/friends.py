from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError
from typing import List

from main.deps import get_current_user
from main.database import relationships_collection, profiles_collection

router = APIRouter(prefix="/friends", tags=["Friends"])


# =======================
# SCHEMA
# =======================

class UsernamePayload(BaseModel):
    username: str


# =======================
# HELPERS
# =======================

def get_username(user: dict) -> str:
    username = user.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return username.lower()


# =======================
# FOLLOW / REQUEST
# =======================

@router.post("/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    from_username = get_username(user)
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

    blocked = await relationships_collection.find_one({
        "from_username": to_username,
        "to_username": from_username,
        "status": "blocked"
    })
    if blocked:
        raise HTTPException(403, "You are blocked")

    status_value = "pending" if target.get("is_private") else "accepted"
    now = datetime.utcnow()

    try:
        await relationships_collection.insert_one({
            "from_username": from_username,
            "to_username": to_username,
            "status": status_value,
            "created_at": now,
            "updated_at": now
        })
    except DuplicateKeyError:
        raise HTTPException(409, "Request already exists")

    return {"status": status_value}


# =======================
# ACCEPT REQUEST
# =======================

@router.post("/accept")
async def accept_request(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    to_username = get_username(user)
    from_username = payload.username.strip().lower()

    result = await relationships_collection.update_one(
        {
            "from_username": from_username,
            "to_username": to_username,
            "status": "pending"
        },
        {
            "$set": {
                "status": "accepted",
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Pending request not found")

    return {"status": "accepted"}


# =======================
# REJECT REQUEST
# =======================

@router.post("/reject")
async def reject_request(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    to_username = get_username(user)
    from_username = payload.username.strip().lower()

    result = await relationships_collection.delete_one({
        "from_username": from_username,
        "to_username": to_username,
        "status": "pending"
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Request not found")

    return {"status": "rejected"}


# =======================
# UNFOLLOW
# =======================

@router.post("/unfollow")
async def unfollow(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    me = get_username(user)
    target = payload.username.strip().lower()

    result = await relationships_collection.delete_one({
        "from_username": me,
        "to_username": target
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Not following")

    return {"status": "unfollowed"}


# =======================
# REMOVE FOLLOWER
# =======================

@router.post("/remove-follower")
async def remove_follower(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    me = get_username(user)
    follower = payload.username.strip().lower()

    result = await relationships_collection.delete_one({
        "from_username": follower,
        "to_username": me
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Follower not found")

    return {"status": "removed"}


# =======================
# BLOCK USER
# =======================

@router.post("/block")
async def block_user(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    me = get_username(user)
    target = payload.username.strip().lower()

    if me == target:
        raise HTTPException(400, "Cannot block yourself")

    await relationships_collection.delete_many({
        "$or": [
            {"from_username": me, "to_username": target},
            {"from_username": target, "to_username": me}
        ]
    })

    try:
        await relationships_collection.insert_one({
            "from_username": me,
            "to_username": target,
            "status": "blocked",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
    except DuplicateKeyError:
        pass

    return {"status": "blocked"}


# =======================
# LIST FOLLOWING
# =======================

@router.get("/following")
async def list_following(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"from_username": username, "status": "accepted"},
        {"_id": 0, "to_username": 1}
    )

    users = [d["to_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# =======================
# LIST FOLLOWERS
# =======================

@router.get("/followers")
async def list_followers(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "accepted"},
        {"_id": 0, "from_username": 1}
    )

    users = [d["from_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# =======================
# LIST PENDING REQUESTS
# =======================

@router.get("/requests")
async def list_requests(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "pending"},
        {"_id": 0, "from_username": 1}
    )

    users = [d["from_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# =======================
# SINGLE STATUS
# =======================

@router.get("/status/{username}")
async def relationship_status(
    username: str,
    user=Depends(get_current_user)
):
    viewer = get_username(user)
    target = username.strip().lower()

    if viewer == target:
        return {"status": "self"}

    outgoing = await relationships_collection.find_one(
        {"from_username": viewer, "to_username": target},
        {"status": 1}
    )

    if outgoing:
        return {
            "status": "following" if outgoing["status"] == "accepted" else outgoing["status"]
        }

    incoming = await relationships_collection.find_one(
        {
            "from_username": target,
            "to_username": viewer,
            "status": "pending"
        }
    )

    if incoming:
        return {"status": "incoming_request"}

    return {"status": "none"}


# =======================
# 🔥 BATCH STATUS (NEW)
# =======================

@router.post("/status/batch")
async def batch_relationship_status(
    usernames: List[str],
    user=Depends(get_current_user)
):
    viewer = get_username(user)

    targets = list({
        u.strip().lower()
        for u in usernames
        if u.strip().lower() and u.strip().lower() != viewer
    })

    if not targets:
        return {}

    status_map = {}

    # outgoing relationships
    cursor = relationships_collection.find(
        {
            "from_username": viewer,
            "to_username": {"$in": targets}
        },
        {"_id": 0, "to_username": 1, "status": 1}
    )

    async for d in cursor:
        status_map[d["to_username"]] = (
            "following" if d["status"] == "accepted" else d["status"]
        )

    # incoming pending requests
    cursor = relationships_collection.find(
        {
            "from_username": {"$in": targets},
            "to_username": viewer,
            "status": "pending"
        },
        {"_id": 0, "from_username": 1}
    )

    async for d in cursor:
        status_map.setdefault(d["from_username"], "incoming_request")

    return {u: status_map.get(u, "none") for u in targets}


# =======================
# USER SEARCH
# =======================

@router.get("/users")
async def list_users(
    q: str = "",
    skip: int = 0,
    limit: int = 10,
    user=Depends(get_current_user)
):
    viewer = get_username(user)

    query = (
        {"username": {"$regex": f"^{q}", "$options": "i"}}
        if q else {}
    )

    cursor = (
        profiles_collection
        .find(query, {"_id": 0, "username": 1, "is_private": 1})
        .sort("username", 1)
        .skip(skip)
        .limit(limit)
    )

    users = []
    async for p in cursor:
        if p["username"] != viewer:
            users.append(p)

    return users

# =======================
# NOTIFICATIONS
# =======================

@router.get("/notifications")
async def notifications(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {
            "to_username": username,
            "status": "pending"
        },
        {
            "_id": 0,
            "from_username": 1,
            "created_at": 1
        }
    ).sort("created_at", -1)

    return [
        {
            "type": "follow_request",
            "from": d["from_username"],
            "created_at": d["created_at"]
        }
        async for d in cursor
    ]
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from main.deps import get_current_user
from main.database import relationships_collection, profiles_collection

router = APIRouter(prefix="/friends", tags=["Friends"])


# ---------- SCHEMA ----------

class UsernamePayload(BaseModel):
    username: str


# ---------- HELPERS ----------

def get_username(user: dict) -> str:
    username = user.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return username


# ---------- FOLLOW / REQUEST ----------

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


# ---------- ACCEPT REQUEST ----------

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


# ---------- REJECT REQUEST ----------

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


# ---------- REMOVE / UNFOLLOW ----------

@router.post("/remove")
async def remove_relationship(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    from_username = get_username(user)
    to_username = payload.username.strip().lower()

    result = await relationships_collection.delete_one({
        "from_username": from_username,
        "to_username": to_username
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Relationship not found")

    return {"status": "removed"}


# ---------- LIST FOLLOWING ----------

@router.get("/following")
async def list_following(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"from_username": username, "status": "accepted"},
        {"_id": 0, "to_username": 1}
    )

    users = [d["to_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# ---------- LIST FOLLOWERS ----------

@router.get("/followers")
async def list_followers(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "accepted"},
        {"_id": 0, "from_username": 1}
    )

    users = [d["from_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# ---------- LIST PENDING ----------

@router.get("/requests")
async def list_requests(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "pending"},
        {"_id": 0, "from_username": 1}
    )

    users = [d["from_username"] async for d in cursor]
    return {"count": len(users), "users": users}


# ---------- RELATIONSHIP STATUS ----------

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
        return {"status": outgoing["status"]}

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


# ---------- LIST USERS (SEARCH + PAGINATION) ----------

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


# ---------- INCOMING (MINIMAL) ----------

@router.get("/incoming")
async def incoming_requests(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "pending"},
        {"_id": 0, "from_username": 1}
    )

    return [d["from_username"] async for d in cursor]
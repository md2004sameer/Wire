from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from main.deps import get_current_user
from main.database import (
    relationships_collection,
    profiles_collection
)

router = APIRouter(prefix="/friends", tags=["Friends"])


# ---------------- SCHEMA ----------------

class UsernamePayload(BaseModel):
    username: str


# ---------------- HELPERS ----------------

def get_username(user: dict) -> str:
    username = user.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    return username


# ---------------- FOLLOW / REQUEST ----------------

@router.post("/follow")
async def follow_user(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    from_username = get_username(user)
    to_username = payload.username.strip()

    if not to_username:
        raise HTTPException(status_code=400, detail="Username required")

    if from_username == to_username:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    target_profile = await profiles_collection.find_one(
        {"username": to_username},
        {"_id": 1, "is_private": 1}
    )

    if not target_profile:
        raise HTTPException(status_code=404, detail="User not found")

    status_value = "pending" if target_profile.get("is_private") else "accepted"
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
        raise HTTPException(
            status_code=409,
            detail="Follow request already exists"
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to create follow request"
        )

    return {"status": status_value}


# ---------------- ACCEPT REQUEST ----------------

@router.post("/accept")
async def accept_request(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    to_username = get_username(user)
    from_username = payload.username.strip()

    if not from_username:
        raise HTTPException(status_code=400, detail="Username required")

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
        raise HTTPException(
            status_code=404,
            detail="Pending request not found"
        )

    return {"status": "accepted"}


# ---------------- REMOVE / UNFOLLOW ----------------

@router.post("/remove")
async def remove_relationship(
    payload: UsernamePayload,
    user=Depends(get_current_user)
):
    from_username = get_username(user)
    to_username = payload.username.strip()

    if not to_username:
        raise HTTPException(status_code=400, detail="Username required")

    result = await relationships_collection.delete_one({
        "from_username": from_username,
        "to_username": to_username
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Relationship not found"
        )

    return {"status": "removed"}


# ---------------- LIST FOLLOWING ----------------

@router.get("/following")
async def list_following(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"from_username": username, "status": "accepted"},
        {"_id": 0, "to_username": 1}
    )

    return {
        "count": await relationships_collection.count_documents(
            {"from_username": username, "status": "accepted"}
        ),
        "users": [doc["to_username"] async for doc in cursor]
    }


# ---------------- LIST FOLLOWERS ----------------

@router.get("/followers")
async def list_followers(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "accepted"},
        {"_id": 0, "from_username": 1}
    )

    return {
        "count": await relationships_collection.count_documents(
            {"to_username": username, "status": "accepted"}
        ),
        "users": [doc["from_username"] async for doc in cursor]
    }


# ---------------- LIST PENDING REQUESTS ----------------

@router.get("/requests")
async def list_requests(user=Depends(get_current_user)):
    username = get_username(user)

    cursor = relationships_collection.find(
        {"to_username": username, "status": "pending"},
        {"_id": 0, "from_username": 1}
    )

    return {
        "count": await relationships_collection.count_documents(
            {"to_username": username, "status": "pending"}
        ),
        "users": [doc["from_username"] async for doc in cursor]
    }


# ---------------- RELATIONSHIP STATUS ----------------

@router.get("/status/{username}")
async def relationship_status(
    username: str,
    user=Depends(get_current_user)
):
    viewer = get_username(user)
    target = username.strip()

    if not target:
        raise HTTPException(status_code=400, detail="Username required")

    if viewer == target:
        return {"status": "self"}

    rel = await relationships_collection.find_one(
        {"from_username": viewer, "to_username": target},
        {"_id": 0, "status": 1}
    )

    if not rel:
        return {"status": "none"}

    return {"status": rel["status"]}
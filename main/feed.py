from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel

from main.database import posts_collection
from main.deps import get_current_user

router = APIRouter(prefix="/posts", tags=["Posts"])


# -------------------------
# Schema
# -------------------------

class PostCreate(BaseModel):
    content: str


# -------------------------
# Create post (AUTH REQUIRED)
# -------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate,
    user=Depends(get_current_user)
):
    content = data.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post content cannot be empty"
        )

    post = {
        "author": user["username"],   # username from cookie-based JWT
        "content": content,
        "created_at": datetime.utcnow()
    }

    await posts_collection.insert_one(post)
    return {"message": "Post created"}


# -------------------------
# Get feed (pagination)
# -------------------------

@router.get("")
async def get_posts(skip: int = 0, limit: int = 10):
    if limit > 50:
        limit = 50   # safety cap

    cursor = (
        posts_collection
        .find({}, {"_id": 0})          # don’t expose Mongo _id
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    return [post async for post in cursor]

@router.get("/latest")
async def latest_post():
    post = await (
        posts_collection
        .find({}, {"_id": 0, "created_at": 1})
        .sort("created_at", -1)
        .limit(1)
        .to_list(1)
    )

    return {
        "latest": post[0]["created_at"] if post else None
    }
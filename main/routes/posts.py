from fastapi import APIRouter, Depends, Query, HTTPException
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field

from main.deps import get_current_user
from main.database import posts_collection, post_likes_collection
from main.services.post_events import broadcast_new_post

router = APIRouter(prefix="/posts", tags=["Posts"])


# ======================
# SCHEMA
# ======================
class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


# ======================
# CREATE POST
# ======================
@router.post("", status_code=201)
async def create_post(
    data: PostCreate,
    user=Depends(get_current_user)
):
    post = {
        "author": user["username"],
        "content": data.content.strip(),
        "created_at": datetime.utcnow(),
        "like_count": 0,
        "comment_count": 0,
        "share_count": 0,
    }

    res = await posts_collection.insert_one(post)

    full_post = {
        "id": str(res.inserted_id),
        **post,
        "liked": False
    }

    # 🔥 broadcast event
    await broadcast_new_post(full_post)

    return full_post


# ======================
# GET FEED
# ======================
@router.get("")
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    after: Optional[datetime] = None,
    user=Depends(get_current_user),
):
    query = {}
    if after:
        query["created_at"] = {"$gt": after}

    cursor = (
        posts_collection
        .find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    posts = []
    async for p in cursor:
        liked = await post_likes_collection.find_one({
            "post_id": p["_id"],
            "username": user["username"]
        })

        posts.append({
            "id": str(p["_id"]),
            "author": p["author"],
            "content": p["content"],
            "created_at": p["created_at"],
            "like_count": p.get("like_count", 0),
            "comment_count": p.get("comment_count", 0),
            "share_count": p.get("share_count", 0),
            "liked": bool(liked),
        })

    return posts
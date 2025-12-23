from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from main.ws_manager import manager

from main.deps import get_current_user
from main.database import (
    posts_collection,
    post_likes_collection,
    post_comments_collection,
    notifications_collection,
)

router = APIRouter(prefix="/posts", tags=["Posts"])


# ======================
# SCHEMAS
# ======================

class PostCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


# ======================
# CREATE POST
# ======================


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
        oid = p["_id"]

        liked = await post_likes_collection.find_one({
            "post_id": oid,
            "username": user["username"]
        })

        posts.append({
            "id": str(oid),
            "author": p["author"],
            "content": p["content"],
            "created_at": p["created_at"],
            "like_count": p.get("like_count", 0),
            "comment_count": p.get("comment_count", 0),
            "share_count": p.get("share_count", 0),
            "liked": bool(liked),
        })

    return posts


# ======================
# LIKE / UNLIKE POST
# ======================

@router.post("/{post_id}/like")
async def toggle_like(
    post_id: str,
    user=Depends(get_current_user)
):
    if not ObjectId.is_valid(post_id):
        raise HTTPException(400, "Invalid post id")

    oid = ObjectId(post_id)
    username = user["username"]

    post = await posts_collection.find_one({"_id": oid})
    if not post:
        raise HTTPException(404, "Post not found")

    existing = await post_likes_collection.find_one({
        "post_id": oid,
        "username": username
    })

    # ---------- UNLIKE ----------
    if existing:
        await post_likes_collection.delete_one({"_id": existing["_id"]})

        await posts_collection.update_one(
            {"_id": oid, "like_count": {"$gt": 0}},
            {"$inc": {"like_count": -1}}
        )

        return {"status": "unliked"}

    # ---------- LIKE ----------
    await post_likes_collection.insert_one({
        "post_id": oid,
        "username": username,
        "created_at": datetime.utcnow()
    })

    await posts_collection.update_one(
        {"_id": oid},
        {"$inc": {"like_count": 1}}
    )

    # ---------- NOTIFICATION ----------
    if post["author"] != username:
        await notifications_collection.insert_one({
            "to_username": post["author"],
            "from_username": username,
            "type": "like",
            "post_id": post_id,
            "created_at": datetime.utcnow(),
            "seen": False,
        })

    return {"status": "liked"}


# ======================
# ADD COMMENT
# ======================

@router.post("/{post_id}/comment")
async def add_comment(
    post_id: str,
    payload: CommentCreate,
    user=Depends(get_current_user)
):
    if not ObjectId.is_valid(post_id):
        raise HTTPException(400, "Invalid post id")

    oid = ObjectId(post_id)

    post = await posts_collection.find_one({"_id": oid})
    if not post:
        raise HTTPException(404, "Post not found")

    res = await post_comments_collection.insert_one({
        "post_id": oid,
        "author": user["username"],
        "text": payload.text.strip(),
        "created_at": datetime.utcnow()
    })

    if res.inserted_id:
        await posts_collection.update_one(
            {"_id": oid},
            {"$inc": {"comment_count": 1}}
        )

        if post["author"] != user["username"]:
            await notifications_collection.insert_one({
                "to_username": post["author"],
                "from_username": user["username"],
                "type": "comment",
                "post_id": post_id,
                "created_at": datetime.utcnow(),
                "seen": False,
            })

    return {"status": "ok"}


# ======================
# GET COMMENTS
# ======================

@router.get("/{post_id}/comments")
async def get_comments(
    post_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    user=Depends(get_current_user)
):
    if not ObjectId.is_valid(post_id):
        raise HTTPException(400, "Invalid post id")

    oid = ObjectId(post_id)

    cursor = (
        post_comments_collection
        .find({"post_id": oid})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )

    comments = []
    async for c in cursor:
        comments.append({
            "id": str(c["_id"]),
            "author": c["author"],
            "text": c["text"],
            "created_at": c["created_at"],
        })

    return comments


@router.post("", status_code=201)
async def create_post(
    data: PostCreate,
    user=Depends(get_current_user)
):
    now = datetime.utcnow()

    post = {
        "author": user["username"],
        "content": data.content.strip(),
        "created_at": now,
        "like_count": 0,
        "comment_count": 0,
        "share_count": 0,
    }

    res = await posts_collection.insert_one(post)

    full_post = {
        "id": str(res.inserted_id),
        "author": post["author"],
        "content": post["content"],
        "created_at": now.isoformat(),  # 🔥 FIX
        "like_count": 0,
        "comment_count": 0,
        "share_count": 0,
        "liked": False,
    }

    print("📢 broadcasting to", len(manager.active), "clients")

    await manager.broadcast({
        "type": "new_post",
        "post": full_post
    })

    return full_post
# ======================
# SHARE POST
# ======================

@router.post("/{post_id}/share")
async def share_post(
    post_id: str,
    user=Depends(get_current_user)
):
    if not ObjectId.is_valid(post_id):
        raise HTTPException(400, "Invalid post id")

    oid = ObjectId(post_id)

    result = await posts_collection.update_one(
        {"_id": oid},
        {"$inc": {"share_count": 1}}
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Post not found")

    return {"status": "shared"}
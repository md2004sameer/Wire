from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, Field

from main.deps import get_current_user
from main.database import posts_collection, post_comments_collection

router = APIRouter(prefix="/posts", tags=["Comments"])


class CommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


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

    await post_comments_collection.insert_one({
        "post_id": oid,
        "author": user["username"],
        "text": payload.text.strip(),
        "created_at": datetime.utcnow()
    })

    await posts_collection.update_one(
        {"_id": oid},
        {"$inc": {"comment_count": 1}}
    )

    return {"status": "ok"}


@router.get("/{post_id}/comments")
async def get_comments(
    post_id: str,
    skip: int = Query(0),
    limit: int = Query(20),
    user=Depends(get_current_user)
):
    if not ObjectId.is_valid(post_id):
        raise HTTPException(400, "Invalid post id")

    cursor = (
        post_comments_collection
        .find({"post_id": ObjectId(post_id)})
        .sort("created_at", 1)
        .skip(skip)
        .limit(limit)
    )

    return [
        {
            "id": str(c["_id"]),
            "author": c["author"],
            "text": c["text"],
            "created_at": c["created_at"],
        }
        async for c in cursor
    ]
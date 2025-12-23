from fastapi import APIRouter, Depends
from datetime import datetime
from pydantic import BaseModel
from main.database import posts_collection
from main.deps import get_current_user

router = APIRouter(prefix="/posts", tags=["Posts"])


class PostCreate(BaseModel):
    content: str


# -------------------------
# Create post (AUTH REQUIRED)
# -------------------------
@router.post("")
async def create_post(
    data: PostCreate,
    user=Depends(get_current_user)
):
    post = {
        "author": user["username"],
        "content": data.content,
        "created_at": datetime.utcnow()
    }

    await posts_collection.insert_one(post)
    return {"message": "Post created"}


# -------------------------
# Get feed (pagination)
# -------------------------
@router.get("")
async def get_posts(skip: int = 0, limit: int = 10):
    cursor = (
        posts_collection
        .find()
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )

    posts = []
    async for p in cursor:
        posts.append({
            "id": str(p["_id"]),
            "author": p["author"],
            "content": p["content"]
        })

    return posts
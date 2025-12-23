from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from main.deps import get_current_user
from main.database import profiles_collection

router = APIRouter(prefix="/profile", tags=["Profile"])


# ======================
# SCHEMAS
# ======================

class ProfileUpdate(BaseModel):
    bio: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    is_private: Optional[bool] = None


# ======================
# HELPERS
# ======================

def get_username(user: dict) -> str:
    username = user.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return username


def default_profile(username: str) -> dict:
    """Returned when profile does not yet exist"""
    return {
        "username": username,
        "bio": "",
        "website": "",
        "location": "",
        "avatar_url": None,
        "is_private": False,
        "created_at": None,
        "updated_at": None,
    }


# ======================
# GET MY PROFILE
# ======================

@router.get("/me")
async def get_my_profile(user=Depends(get_current_user)):
    username = get_username(user)

    profile = await profiles_collection.find_one(
        {"username": username},
        {"_id": 0}
    )

    # 🔥 IMPORTANT: do NOT return 404
    if not profile:
        return default_profile(username)

    return profile


# ======================
# CREATE / UPDATE PROFILE (UPSERT)
# ======================

@router.put("/me")
async def update_profile(
    payload: ProfileUpdate,
    user=Depends(get_current_user)
):
    username = get_username(user)

    update_data = payload.dict(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )

    now = datetime.utcnow()

    await profiles_collection.update_one(
        {"username": username},
        {
            "$set": {
                **update_data,
                "updated_at": now
            },
            "$setOnInsert": {
                "username": username,
                "created_at": now
            }
        },
        upsert=True
    )

    return {"status": "saved"}
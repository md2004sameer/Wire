from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

from main.deps import get_current_user
from main.database import profiles_collection

router = APIRouter(prefix="/profile", tags=["Profile"])


# -------------------- SCHEMA --------------------

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    is_private: Optional[bool] = None


# -------------------- UTILITY --------------------

def get_username(user: dict) -> str:
    username = user.get("username")
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid token: username missing"
        )
    return username


# -------------------- GET MY PROFILE --------------------

@router.get("/me")
async def get_my_profile(user=Depends(get_current_user)):
    username = get_username(user)

    profile = await profiles_collection.find_one(
        {"username": username},
        {"_id": 0}
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


# -------------------- CREATE / UPDATE PROFILE (UPSERT) --------------------

@router.put("/me")
async def update_profile(
    payload: ProfileUpdate,
    user=Depends(get_current_user)
):
    username = get_username(user)

    update_data = {
        k: v for k, v in payload.dict().items()
        if v is not None
    }

    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

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
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from main.database import users_collection, profiles_collection
from main.models import UserSignup, UserLogin
from main.security import hash_password, verify_password, create_access_token
from main.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(data: UserSignup):
    existing = await users_collection.find_one({
        "$or": [
            {"email": data.email},
            {"username": data.username}
        ]
    })

    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    user = {
        "username": data.username,
        "email": data.email,
        "password": hash_password(data.password),
    }

    result = await users_collection.insert_one(user)

    profile = {
        "user_id": result.inserted_id,
        "username": data.username,
        "full_name": "",
        "bio": "",
        "gender": "prefer_not_say",
        "date_of_birth": None,
        "website": "",
        "location": "",
        "avatar_url": "",
        "is_private": False,
        "friends": [],
        "friend_requests": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    await profiles_collection.insert_one(profile)

    return {"message": "Account created successfully"}

@router.post("/login")
async def login(data: UserLogin):
    user = await users_collection.find_one({"email": data.email})

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "user_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
    })

    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return user
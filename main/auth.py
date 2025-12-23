from fastapi import APIRouter, HTTPException, status, Response, Depends
from datetime import datetime
from pymongo.errors import DuplicateKeyError
import os

from main.database import users_collection, profiles_collection
from main.models import UserSignup, UserLogin
from main.security import hash_password, verify_password, create_access_token
from main.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])

ENV = os.getenv("ENV", "development")


# ======================
# ME (COOKIE AUTH)
# ======================

@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {
        "username": user["username"],
        "email": user.get("email")
    }


# ======================
# SIGNUP
# ======================

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(data: UserSignup):
    email = data.email.strip().lower()
    username = data.username.strip().lower()

    try:
        await users_collection.insert_one({
            "email": email,
            "username": username,
            "password": hash_password(data.password),
            "created_at": datetime.utcnow()
        })
    except DuplicateKeyError as e:
        msg = str(e)
        if "email" in msg:
            raise HTTPException(409, "Email already registered")
        if "username" in msg:
            raise HTTPException(409, "Username already taken")
        raise HTTPException(409, "User already exists")

    await profiles_collection.insert_one({
        "username": username,
        "full_name": "",
        "bio": "",
        "gender": "prefer_not_say",
        "date_of_birth": None,
        "website": "",
        "location": "",
        "avatar_url": "",
        "is_private": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    return {"message": "Account created successfully"}


# ======================
# LOGIN (COOKIE)
# ======================

@router.post("/login")
async def login(data: UserLogin, response: Response):
    email = data.email.strip().lower()

    user = await users_collection.find_one({"email": email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "username": user["username"],
        "email": user["email"]
    })

    cookie_kwargs = {
        "key": "access_token",
        "value": token,
        "httponly": True,
        "max_age": 60 * 60 * 24
    }

    # 🔥 ENV-AWARE COOKIE SETTINGS
    if ENV == "production":
        cookie_kwargs.update({
            "secure": True,     # HTTPS only (ngrok / prod)
            "samesite": "none"
        })
    else:
        cookie_kwargs.update({
            "secure": False,    # Local HTTP
            "samesite": "lax"
        })

    response.set_cookie(**cookie_kwargs)

    return {"message": "Login successful"}


# ======================
# LOGOUT
# ======================

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
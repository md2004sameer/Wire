from fastapi import APIRouter, HTTPException, status, Response
from datetime import datetime
from pymongo.errors import DuplicateKeyError

from main.database import users_collection, profiles_collection
from main.models import UserSignup, UserLogin
from main.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------- SIGNUP ----------------

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

    # auto-create profile
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


# ---------------- LOGIN ----------------

@router.post("/login")
async def login(data: UserLogin, response: Response):
    email = data.email.strip().lower()

    user = await users_collection.find_one({"email": email})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token = create_access_token({
        "username": user["username"],
        "email": user["email"]
    })

    # ✅ HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,      # True in production (HTTPS)
        samesite="lax",
        max_age=60 * 60 * 24
    )

    return {"message": "Login successful"}


# ---------------- LOGOUT ----------------

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}
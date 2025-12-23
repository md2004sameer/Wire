from fastapi import APIRouter, HTTPException
from main.database import users_collection
from main.models import UserSignup, UserLogin
from main.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# -------------------------
# Signup
# -------------------------
@router.post("/signup")
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
        "password": hash_password(data.password)
    }

    await users_collection.insert_one(user)
    return {"message": "Account created successfully"}

# -------------------------
# Login
# -------------------------
@router.post("/login")
async def login(data: UserLogin):
    user = await users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if "password" not in user:
        raise HTTPException(
            status_code=500,
            detail="User record is corrupted. Please re-signup."
        )

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
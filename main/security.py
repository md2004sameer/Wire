from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
import os

# -------------------------
# Password hashing
# -------------------------
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        ph.verify(hashed, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False


# -------------------------
# JWT config
# -------------------------
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# -------------------------
# JWT creation
# -------------------------
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------
# JWT decoding
# -------------------------
def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except JWTError:
        raise ValueError("Invalid token")
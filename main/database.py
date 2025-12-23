from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set")

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000
)

db = client["wire"]

# ---------- COLLECTIONS ----------
users_collection = db["users"]
posts_collection = db["posts"]
profiles_collection = db["profiles"]
relationships_collection = db["relationships"]


# ---------- INDEXES ----------
async def init_indexes():

    # -------- USERS --------
    await users_collection.create_index(
        "email",
        unique=True,
        collation={"locale": "en", "strength": 2}
    )

    await users_collection.create_index(
        "username",
        unique=True,
        collation={"locale": "en", "strength": 2}
    )

    # -------- PROFILES --------
    await profiles_collection.create_index(
        "username",
        unique=True,
        collation={"locale": "en", "strength": 2}
    )

    # -------- RELATIONSHIPS (FOLLOW SYSTEM) --------
    await relationships_collection.create_index(
        [("from_username", 1), ("to_username", 1)],
        unique=True,
        collation={"locale": "en", "strength": 2}
    )

    # Query optimization
    await relationships_collection.create_index(
        [("to_username", 1), ("status", 1)]
    )

    await relationships_collection.create_index(
        [("from_username", 1), ("status", 1)]
    )

    # -------- POSTS --------
    await posts_collection.create_index(
        [("created_at", -1)]
    )
from dotenv import load_dotenv
load_dotenv()

import os
from motor.motor_asyncio import AsyncIOMotorClient

# ======================
# MONGO CONNECTION
# ======================

MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set")

DB_NAME = os.getenv("DB_NAME", "wire")

client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000
)

db = client[DB_NAME]

# ======================
# COLLECTIONS
# ======================

users_collection = db["users"]
profiles_collection = db["profiles"]

relationships_collection = db["relationships"]

posts_collection = db["posts"]

# ---------- SOCIAL INTERACTIONS ----------
post_likes_collection = db["post_likes"]
post_comments_collection = db["post_comments"]
post_shares_collection = db["post_shares"]

# ---------- NOTIFICATIONS ----------
notifications_collection = db["notifications"]

# ======================
# INDEXES
# ======================

async def init_indexes():
    """
    Ensure all MongoDB indexes.
    Safe to call multiple times.
    """

    # ---------- USERS ----------
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

    # ---------- PROFILES ----------
    await profiles_collection.create_index(
        "username",
        unique=True,
        collation={"locale": "en", "strength": 2}
    )

    # ---------- RELATIONSHIPS ----------
    await relationships_collection.create_index(
        [("from_username", 1), ("to_username", 1)],
        unique=True,
        collation={"locale": "en", "strength": 2}
    )
    await relationships_collection.create_index(
        [("to_username", 1), ("status", 1)]
    )
    await relationships_collection.create_index(
        [("from_username", 1), ("status", 1)]
    )

    # ---------- POSTS ----------
    # Feed sorting & polling
    await posts_collection.create_index(
        [("created_at", -1)]
    )
    await posts_collection.create_index(
        [("author", 1), ("created_at", -1)]
    )

    # ---------- POST LIKES ----------
    # Prevent duplicate likes
    await post_likes_collection.create_index(
        [("post_id", 1), ("username", 1)],
        unique=True
    )
    await post_likes_collection.create_index(
        [("post_id", 1)]
    )

    # ---------- POST COMMENTS ----------
    await post_comments_collection.create_index(
        [("post_id", 1), ("created_at", 1)]
    )

    # ---------- POST SHARES ----------
    await post_shares_collection.create_index(
        [("post_id", 1)]
    )

    # ---------- NOTIFICATIONS ----------
    await notifications_collection.create_index(
        [("to_username", 1), ("created_at", -1)]
    )
    await notifications_collection.create_index(
        [("to_username", 1), ("seen", 1)]
    )
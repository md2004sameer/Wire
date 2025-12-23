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

users_collection = db["users"]
posts_collection = db["posts"]
profiles_collection = db["profiles"]


async def init_indexes():
    # -------- USERS --------
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("username", unique=True)

    # -------- PROFILES --------
    await profiles_collection.create_index("username", unique=True)

    # -------- POSTS --------
    await posts_collection.create_index("created_at")
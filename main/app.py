from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from main.auth import router as auth_router
from main.feed import router as feed_router
from main.ws import router as ws_router
from main.profile import router as profile_router
from main.database import init_indexes

print("🔥 Wire App Loaded 🔥")

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_indexes()
    print("✅ MongoDB indexes ensured")

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def landing_page():
    return FileResponse(STATIC_DIR / "landing.html")

@app.get("/profile")
def profile_page():
    return FileResponse(STATIC_DIR / "profile.html")

@app.get("/signup")
def signup_page():
    return FileResponse(STATIC_DIR / "signup.html")

@app.get("/login")
def login_page():
    return FileResponse(STATIC_DIR / "login.html")

@app.get("/home")
def home_page():
    return FileResponse(STATIC_DIR / "home.html")

app.include_router(auth_router)
app.include_router(feed_router)
app.include_router(ws_router)
app.include_router(profile_router)
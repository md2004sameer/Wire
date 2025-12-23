from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from main.auth import router as auth_router
from main.feed import router as feed_router
from main.ws import router as ws_router

print("🔥 Wire App Loaded 🔥")

app = FastAPI()

# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

# -------------------------
# Static Files
# -------------------------
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# -------------------------
# Pages (PUBLIC)
# -------------------------
@app.get("/")
def landing_page():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/signup")
def signup_page():
    return FileResponse(STATIC_DIR / "signup.html")

@app.get("/login")
def login_page():
    return FileResponse(STATIC_DIR / "login.html")

@app.get("/home")
def home_page():
    # Auth enforced via API calls + JS token check
    return FileResponse(STATIC_DIR / "home.html")

# -------------------------
# Routers (JWT enforced inside APIs)
# -------------------------
app.include_router(auth_router)
app.include_router(feed_router)
app.include_router(ws_router)
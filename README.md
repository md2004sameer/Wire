Wire

Wire is a real-time social networking web application built with FastAPI, MongoDB, and vanilla JavaScript, focused on simplicity, speed, and clean architecture.
It supports posts, likes, comments, followers, notifications, profiles, and real-time updates using WebSockets with a polling fallback.

⸻

Features

🧵 Feed
	•	Create text posts
	•	Infinite scrolling feed
	•	Like and comment on posts
	•	Real-time post updates using WebSockets
	•	Automatic fallback to REST polling if WebSocket disconnects

💬 Comments
	•	Add comments to posts
	•	View comments in a modal
	•	Comment count updates instantly

👥 Friends / Users
	•	Explore all users
	•	Follow / unfollow users
	•	Private accounts with follow requests
	•	Followers & following lists
	•	Relationship status tracking (none, pending, accepted)

🔔 Notifications
	•	Follow requests
	•	Follow accepted
	•	Likes and comments
	•	Grouped by day (Today / Yesterday / Date)
	•	Real-time delivery support (ready for extension)

👤 Profile
	•	View and edit profile
	•	Bio, website, location, privacy toggle
	•	Followers / following counts
	•	Logout support

🔐 Authentication
	•	Cookie-based authentication
	•	Protected routes
	•	Automatic redirect to login on session expiry

⸻

Tech Stack

Backend
	•	FastAPI
	•	MongoDB (Motor async driver)
	•	JWT authentication
	•	WebSockets for real-time feed
	•	Clean modular routers (posts, friends, profile, notifications)

Frontend
	•	Vanilla JavaScript (no frameworks)
	•	HTML + CSS
	•	Modular JS files:
	•	auth.js
	•	feed.js
	•	comments.js
	•	profile.js
	•	notifications.js

⸻

Architecture Overview

Frontend (HTML + JS)
        |
        | REST (fetch)
        | WebSocket (feed)
        v
FastAPI Backend
        |
        v
MongoDB

Real-Time Strategy
	•	WebSocket for instant post delivery
	•	Polling fallback every 10s if WS disconnects
	•	REST remains the source of truth

⸻

Project Structure

backend/
 ├── main/
 │   ├── app.py
 │   ├── deps.py
 │   ├── database.py
 │   ├── ws_manager.py
 │   └── routers/
 │       ├── auth.py
 │       ├── posts.py
 │       ├── friends.py
 │       ├── profile.py
 │       └── notifications.py

frontend/
 ├── templates/
 │   ├── home.html
 │   ├── profile.html
 │   ├── users.html
 │   ├── notifications.html
 │   └── login.html
 └── static/
     ├── js/
     │   ├── auth.js
     │   ├── feed.js
     │   ├── comments.js
     │   ├── profile.js
     │   └── notifications.js
     └── css/
         ├── home.css
         ├── profile.css
         └── theme.css


⸻

Setup Instructions

1️⃣ Clone Repository

git clone <repo-url>
cd wire

2️⃣ Create Virtual Environment

python -m venv .venv
source .venv/bin/activate   # macOS/Linux

3️⃣ Install Dependencies

pip install -r requirements.txt

4️⃣ Environment Variables

Create .env:

MONGO_URI=mongodb://localhost:27017
JWT_SECRET=your_secret_key

5️⃣ Run Server

python -m uvicorn main.app:app --reload

Open:
👉 http://127.0.0.1:8000



Current Status
	•	✅ Core social features implemented
	•	✅ Real-time feed working
	•	✅ Stable friend system
	•	🔄 Notifications ready for live WS extension
	•	🔜 Media posts, search, and performance tuning planned



import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import SYSTEM_USER_ID
from database import test_connection
from material_cache import preload_system_materials

load_dotenv()

print("=" * 60)
print("Starting FastAPI application...")
print("=" * 60)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ── Dev-mode auth routes (local login/register without Supabase) ──
from auth import AUTH_MODE

if AUTH_MODE == "local":
    from routers import dev_auth
    app.include_router(dev_auth.router)

# ── Domain routers ─────────────────────────────────────────────
from routers import debug, chat, care_plans, materials, learning_plans, profile, admin

app.include_router(debug.router)
app.include_router(chat.router)
app.include_router(care_plans.router)
app.include_router(materials.router)
app.include_router(learning_plans.router)
app.include_router(profile.router)
app.include_router(admin.router)


# ── Startup ────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    print("\n" + "=" * 60)
    print("Running startup tasks...")
    print(f"AUTH_MODE = {AUTH_MODE}")
    print("=" * 60)

    try:
        print("\n[1/3] Testing database connection...")
        if test_connection():
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
            return
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        import traceback
        traceback.print_exc()
        return

    try:
        print("\n[2/3] Preloading system materials...")
        from database import get_session_local
        db = get_session_local()()
        try:
            preload_system_materials(db, SYSTEM_USER_ID)
            print("✓ Material cache initialized")
        finally:
            db.close()
    except Exception as e:
        print(f"✗ Warning: Could not preload system materials: {e}")
        import traceback
        traceback.print_exc()

    print("\n[3/3] Startup complete!")
    print("=" * 60)
    print("Server ready at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    print("=" * 60 + "\n")

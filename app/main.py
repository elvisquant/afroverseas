from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine, Base
from . import models
from .routers import public, admin, leads

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afroverseas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(public.router)
app.include_router(admin.router)
app.include_router(leads.router)

# --- CLEAN PATH LOGIC ---
# __file__ is at /app/app/main.py
# .dirname gets /app/app
# .dirname again gets /app (The Root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/portal-access-admin")
async def read_admin():
    path = os.path.join(BASE_DIR, "admin.html")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Admin Dashboard file missing")
    return FileResponse(path)
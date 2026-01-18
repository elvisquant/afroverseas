from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from .database import engine, Base
from . import models
from .routers import public, admin, leads

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afroverseas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for logo, receipts, and QR codes
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Business Routers
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(leads.router)

# --- ROUTING LOGIC ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/")
async def read_index():
    path = os.path.join(BASE_DIR, "index.html")
    return FileResponse(path)

@app.get("/portal-access-admin")
async def read_admin():
    path = os.path.join(BASE_DIR, "admin.html")
    if not os.path.isfile(path):
        # Professional way to handle missing files
        raise HTTPException(status_code=404, detail="Admin Dashboard file missing on server")
    return FileResponse(path)







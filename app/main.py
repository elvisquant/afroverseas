from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

@app.get("/")
async def read_index():
    """Served for afroverseas.com"""
    return FileResponse('index.html')

@app.get("/portal-access-admin")
async def read_admin():
    """Served for admin.afroverseas.com via Nginx Proxy"""
    return FileResponse('admin.html')







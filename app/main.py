from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import public, admin, leads # Refactored imports



# This command uses Base to create the tables in Postgres
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Afroverseas API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Connect the sub-modules
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(leads.router)

# Serve the high-end Frontend
from fastapi.responses import FileResponse

# 1. Access for Main WebApp
@app.get("/")
async def read_index():
    return FileResponse('index.html')

# 2. Access for Admin Dashboard
@app.get("/portal-access-admin")
async def read_admin():
    return FileResponse('admin.html')
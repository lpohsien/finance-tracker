from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.middleware.gzip import GZipMiddleware
import os
import logging

from api.db import engine, Base
from api.routers import transactions, analytics, configuration, tracking
from api.auth import router as auth_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance Tracker API")

# Add GZip compression to reduce RAM usage during file transfer
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth_router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(configuration.router)
app.include_router(tracking.router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Static Files (Frontend)
# Assuming the React 'dist' folder is at the root level relative to the api folder
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

# Mount the /assets directory specifically for CSS/JS
# This is critical for Vite's generated assets
if os.path.exists(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="static")

# SPA Catch-all Route
@app.get("/{catchall:path}")
async def serve_frontend(catchall: str):
    # Safety check: Do not return index.html for API calls that 404'd
    if catchall.startswith("api/") or catchall.startswith("auth/"):
        return {"error": "Not Found"}

    # Check if the requested path exists as a physical file (e.g., favicon.ico, robots.txt)
    # catchall typically doesn't include leading slash, but we handle it just in case
    file_path = os.path.join(frontend_dist, catchall)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, return index.html to allow React Router to handle the URL
    index_path = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"error": "Frontend build not found. Run 'npm run build' in the frontend directory."}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application started")


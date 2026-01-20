from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import logging

from api.db import engine, Base
from api.routers import transactions, analytics, configuration
from api.auth import router as auth_router

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Finance Tracker API")

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

# Static Files (Frontend)
# Serve "frontend/dist" if it exists (Production)
static_dir = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Allow API calls to pass through
        if full_path.startswith("api/") or full_path.startswith("auth/"):
            return {"error": "Not Found"}

        # Serve index.html for SPA routing
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
             return FileResponse(index_path)
        return {"message": "Frontend not built"}
else:
    @app.get("/")
    def read_root():
        return {"message": "Finance Tracker API Running. Frontend not found (Dev mode?)"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Application started")

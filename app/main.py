"""
Main FastAPI Application Entry Point for Multimodal Attendance & Engagement Agent.
Integrates HTTP routes, WebSocket streams, and static assets.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import config
from app.api.routes import router as http_router
from app.api.websocket import router as ws_router
from app.database import db, seed_data

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes SQLite database and seeds default classroom roster."""
    db.init_db()
    seed_data.seed_database()
    print("Classroom Intelligence System online and database initialized.")
    yield

app = FastAPI(
    title="Multimodal Attendance & Engagement Agent",
    description="AI-powered, privacy-preserving classroom intelligence platform.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local testing and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for CSS, JS, Assets
app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

# Include Routers
app.include_router(http_router)
app.include_router(ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.SERVER_CONFIG["HOST"],
        port=config.SERVER_CONFIG["PORT"],
        reload=config.SERVER_CONFIG["DEBUG"]
    )

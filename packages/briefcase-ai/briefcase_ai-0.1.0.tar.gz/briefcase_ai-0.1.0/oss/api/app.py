"""briefcase-ai FastAPI application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

from .auth import get_current_user, User
from .routers import snapshots, replay, policies
from .websocket import router as websocket_router

# Create FastAPI app with OpenAPI documentation
app = FastAPI(
    title="briefcase-ai API",
    description="""
    Deterministic observability & replay for AI systems

    ## Features

    - **Snapshots**: Capture and store system state snapshots
    - **Replay**: Replay system behavior deterministically
    - **Policies**: Configure and manage observability policies
    - **Real-time**: WebSocket support for live updates

    ## Authentication

    Uses HTTP Basic Authentication for the OSS version.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware for UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    snapshots.router,
    prefix="/api/v1/snapshots",
    tags=["snapshots"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    replay.router,
    prefix="/api/v1/replay",
    tags=["replay"],
    dependencies=[Depends(get_current_user)],
)

app.include_router(
    policies.router,
    prefix="/api/v1/policies",
    tags=["policies"],
    dependencies=[Depends(get_current_user)],
)

# WebSocket endpoint
app.include_router(websocket_router, prefix="/ws")

# Health check endpoint (no auth required)
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "0.1.0"}

# Root endpoint
@app.get("/", tags=["system"])
async def root():
    """Root endpoint with basic info."""
    return {
        "name": "Briefcase OSS API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

# Test authenticated endpoint
@app.get("/auth-test", tags=["system"])
async def auth_test(current_user: User = Depends(get_current_user)):
    """Test authenticated endpoint."""
    return {"message": "Authentication successful", "user": current_user.username}

# Static file serving for UI (when co-located)
ui_build_path = Path(__file__).parent.parent / "ui" / "out"
if ui_build_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_build_path), html=True), name="ui")

def main():
    """Main entry point for running the API server."""
    host = os.getenv("BRIEFCASE_API_HOST", "127.0.0.1")
    port = int(os.getenv("BRIEFCASE_API_PORT", "8000"))

    uvicorn.run(
        "briefcase.api.app:app",
        host=host,
        port=port,
        reload=os.getenv("BRIEFCASE_DEV", "false").lower() == "true",
        log_level="info",
    )

if __name__ == "__main__":
    main()

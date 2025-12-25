"""
Replay API Router

REST endpoints for managing deterministic replay operations.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from enum import Enum
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ..auth import User, get_current_user
from ..websocket import websocket_manager

router = APIRouter()

class ReplayStatus(str, Enum):
    """Replay execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReplayCreate(BaseModel):
    """Request model for creating a replay."""
    name: str = Field(..., description="Human-readable name for the replay")
    snapshot_id: str = Field(..., description="Snapshot to replay from")
    description: Optional[str] = Field(None, description="Optional description")
    config: Dict[str, Any] = Field(default_factory=dict, description="Replay configuration")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")

class ReplayUpdate(BaseModel):
    """Request model for updating replay metadata."""
    name: Optional[str] = Field(None, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    tags: Optional[List[str]] = Field(None, description="Updated tags")

class Replay(BaseModel):
    """Replay model."""
    id: str = Field(..., description="Unique replay identifier")
    name: str = Field(..., description="Human-readable name")
    snapshot_id: str = Field(..., description="Source snapshot ID")
    description: Optional[str] = Field(None, description="Description")
    config: Dict[str, Any] = Field(default_factory=dict, description="Configuration")
    tags: List[str] = Field(default_factory=list, description="Tags")
    status: ReplayStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_by: str = Field(..., description="Creator username")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    results: Dict[str, Any] = Field(default_factory=dict, description="Replay results")

# In-memory storage (replace with database in production)
replays_db: Dict[str, Replay] = {}

@router.get("/", response_model=List[Replay])
async def list_replays(
    skip: int = Query(0, ge=0, description="Number of replays to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of replays to return"),
    status: Optional[ReplayStatus] = Query(None, description="Filter by status"),
    snapshot_id: Optional[str] = Query(None, description="Filter by snapshot ID"),
    current_user: User = Depends(get_current_user)
):
    """
    List all replays with optional filtering and pagination.
    """
    replays_list = list(replays_db.values())

    # Filter by status
    if status:
        replays_list = [r for r in replays_list if r.status == status]

    # Filter by snapshot ID
    if snapshot_id:
        replays_list = [r for r in replays_list if r.snapshot_id == snapshot_id]

    # Sort by creation date (newest first)
    replays_list.sort(key=lambda x: x.created_at, reverse=True)

    # Apply pagination
    return replays_list[skip:skip + limit]

@router.get("/{replay_id}", response_model=Replay)
async def get_replay(
    replay_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific replay by ID.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    return replays_db[replay_id]

@router.post("/", response_model=Replay, status_code=201)
async def create_replay(
    replay_data: ReplayCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new replay.
    """
    replay_id = str(uuid4())

    replay = Replay(
        id=replay_id,
        name=replay_data.name,
        snapshot_id=replay_data.snapshot_id,
        description=replay_data.description,
        config=replay_data.config,
        tags=replay_data.tags,
        status=ReplayStatus.PENDING,
        created_at=datetime.now(),
        created_by=current_user.username,
        progress=0.0
    )

    replays_db[replay_id] = replay

    return replay

@router.post("/{replay_id}/start")
async def start_replay(
    replay_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Start executing a replay.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    replay = replays_db[replay_id]

    if replay.status != ReplayStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start replay in status: {replay.status}"
        )

    # Update replay status
    replay.status = ReplayStatus.RUNNING
    replay.started_at = datetime.now()
    replays_db[replay_id] = replay

    # Notify via WebSocket
    await websocket_manager.notify_replay_started(replay_id, current_user.username)

    # In real implementation, this would trigger actual replay execution
    # For now, we'll simulate completion after a short delay
    import asyncio
    asyncio.create_task(simulate_replay_execution(replay_id))

    return {"message": "Replay started", "replay_id": replay_id}

@router.post("/{replay_id}/stop")
async def stop_replay(
    replay_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Stop a running replay.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    replay = replays_db[replay_id]

    if replay.status != ReplayStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop replay in status: {replay.status}"
        )

    # Update replay status
    replay.status = ReplayStatus.CANCELLED
    replay.completed_at = datetime.now()
    replays_db[replay_id] = replay

    # Notify via WebSocket
    await websocket_manager.notify_replay_completed(replay_id, False, current_user.username)

    return {"message": "Replay stopped", "replay_id": replay_id}

@router.put("/{replay_id}", response_model=Replay)
async def update_replay(
    replay_id: str,
    replay_update: ReplayUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update a replay's metadata.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    replay = replays_db[replay_id]

    # Update only provided fields
    if replay_update.name is not None:
        replay.name = replay_update.name
    if replay_update.description is not None:
        replay.description = replay_update.description
    if replay_update.tags is not None:
        replay.tags = replay_update.tags

    replays_db[replay_id] = replay

    return replay

@router.delete("/{replay_id}", status_code=204)
async def delete_replay(
    replay_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a replay.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    del replays_db[replay_id]

@router.get("/{replay_id}/logs")
async def get_replay_logs(
    replay_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of log entries"),
    current_user: User = Depends(get_current_user)
):
    """
    Get replay execution logs.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    # Placeholder logs (in real implementation, would fetch from log storage)
    logs = [
        {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "message": f"Replay {replay_id} log entry",
            "source": "replay_engine"
        }
    ]

    return {"replay_id": replay_id, "logs": logs}

@router.get("/{replay_id}/results")
async def get_replay_results(
    replay_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get replay execution results.
    """
    if replay_id not in replays_db:
        raise HTTPException(status_code=404, detail="Replay not found")

    replay = replays_db[replay_id]

    if replay.status not in [ReplayStatus.COMPLETED, ReplayStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail="Replay results not available until completion"
        )

    return {
        "replay_id": replay_id,
        "status": replay.status,
        "results": replay.results,
        "execution_time_seconds": (
            (replay.completed_at - replay.started_at).total_seconds()
            if replay.started_at and replay.completed_at
            else None
        )
    }

# Simulation function for demo purposes
async def simulate_replay_execution(replay_id: str):
    """Simulate replay execution with progress updates."""
    import asyncio

    replay = replays_db.get(replay_id)
    if not replay:
        return

    # Simulate progress updates
    for progress in [25, 50, 75, 100]:
        await asyncio.sleep(1)  # Simulate work
        replay.progress = progress
        replays_db[replay_id] = replay

    # Complete the replay
    replay.status = ReplayStatus.COMPLETED
    replay.completed_at = datetime.now()
    replay.results = {
        "operations_replayed": 42,
        "success_rate": 0.98,
        "duration_ms": 1500
    }
    replays_db[replay_id] = replay

    # Notify completion
    await websocket_manager.notify_replay_completed(replay_id, True)
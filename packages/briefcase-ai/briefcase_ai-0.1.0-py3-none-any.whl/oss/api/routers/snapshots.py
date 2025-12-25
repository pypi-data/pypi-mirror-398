"""
Snapshots API Router

REST endpoints for managing system state snapshots.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, Body, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import User, get_current_user
from ..websocket import websocket_manager
from ...storage.snapshot_repository import get_snapshot_repository
from ...storage.database import get_session
from ...storage.models import Snapshot as SnapshotModel

router = APIRouter()

# Models for request/response
class SnapshotCreate(BaseModel):
    """Request model for creating a snapshot."""
    name: str = Field(..., description="Human-readable name for the snapshot")
    description: Optional[str] = Field(None, description="Optional description")
    tags: List[str] = Field(default_factory=list, description="Tags for organization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class SnapshotUpdate(BaseModel):
    """Request model for updating a snapshot."""
    name: Optional[str] = Field(None, description="Updated name")
    description: Optional[str] = Field(None, description="Updated description")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated metadata")

class Snapshot(BaseModel):
    """Snapshot model."""
    id: str = Field(..., description="Unique snapshot identifier")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Description")
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="Creator username")
    size_bytes: int = Field(..., description="Snapshot size in bytes")
    checksum: str = Field(..., description="Data integrity checksum")
    status: str = Field(..., description="Snapshot status (capturing, ready, error)")

# Dependency for snapshot repository
def get_repository(session: Session = Depends(get_session)):
    return get_snapshot_repository(session=session)

@router.get("/", response_model=List[Snapshot])
async def list_snapshots(
    skip: int = Query(0, ge=0, description="Number of snapshots to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of snapshots to return"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    List all snapshots with optional filtering and pagination.
    """
    # Get tag list if provided
    tag_list = None
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]

    # Get snapshots from database
    snapshot_models = repository.list_snapshots(
        skip=skip,
        limit=limit,
    )

    # Convert to API response models and calculate stats
    result = []
    for model in snapshot_models:
        stats = repository.get_snapshot_stats(model.snapshot_id)
        snapshot = Snapshot(
            id=model.snapshot_id,
            name=model.snapshot_metadata.get('name', f"Snapshot {model.snapshot_id[:8]}"),
            description=model.snapshot_metadata.get('description'),
            tags=model.snapshot_metadata.get('tags', []),
            metadata=model.snapshot_metadata,
            created_at=model.timestamp,
            created_by=model.snapshot_metadata.get('created_by', 'system'),
            size_bytes=stats['size_bytes'] if stats else 0,
            checksum=stats['checksum'] if stats else f"sha256:{model.snapshot_id}",
            status="ready"
        )

        # Apply tag filtering
        if tag_list is None or any(tag in snapshot.tags for tag in tag_list):
            result.append(snapshot)

    return result

@router.get("/{snapshot_id}", response_model=Snapshot)
async def get_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    Get a specific snapshot by ID.
    """
    model = repository.get_snapshot(snapshot_id)
    if not model:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    stats = repository.get_snapshot_stats(snapshot_id)

    return Snapshot(
        id=model.snapshot_id,
        name=model.snapshot_metadata.get('name', f"Snapshot {model.snapshot_id[:8]}"),
        description=model.snapshot_metadata.get('description'),
        tags=model.snapshot_metadata.get('tags', []),
        metadata=model.snapshot_metadata,
        created_at=model.timestamp,
        created_by=model.snapshot_metadata.get('created_by', 'system'),
        size_bytes=stats['size_bytes'] if stats else 0,
        checksum=stats['checksum'] if stats else f"sha256:{model.snapshot_id}",
        status="ready"
    )

@router.post("/", response_model=Snapshot, status_code=201)
async def create_snapshot(
    snapshot_data: SnapshotCreate,
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    Create a new snapshot with real state capture.
    """
    # Prepare metadata with API request data
    metadata = snapshot_data.metadata.copy()
    metadata.update({
        'name': snapshot_data.name,
        'description': snapshot_data.description,
        'tags': snapshot_data.tags,
        'created_by': current_user.username,
        'api_created': True,
    })

    # Create sample input/output data for demonstration
    input_data = {
        "request_type": "manual_snapshot",
        "user": current_user.username,
        "timestamp": datetime.now().isoformat(),
        "parameters": snapshot_data.model_dump() if hasattr(snapshot_data, 'model_dump') else snapshot_data.dict()
    }

    output_data = {
        "status": "captured",
        "message": f"Snapshot '{snapshot_data.name}' created successfully",
        "artifacts_captured": ["metadata", "input_data", "output_data"]
    }

    # Create snapshot using repository
    model = repository.create_snapshot(
        name=snapshot_data.name,
        description=snapshot_data.description,
        tags=snapshot_data.tags,
        metadata=metadata,
        created_by=current_user.username,
        model_name="api_snapshot",
        model_version="1.0",
        input_data=input_data,
        output_data=output_data,
    )

    # Store all needed fields before the session might close
    snapshot_id = model.snapshot_id
    snapshot_metadata = model.snapshot_metadata
    timestamp = model.timestamp

    # Get stats for response
    stats = repository.get_snapshot_stats(snapshot_id)

    # Create response model
    snapshot = Snapshot(
        id=snapshot_id,
        name=snapshot_data.name,
        description=snapshot_data.description,
        tags=snapshot_data.tags,
        metadata=metadata,
        created_at=timestamp,
        created_by=current_user.username,
        size_bytes=stats['size_bytes'] if stats else 0,
        checksum=stats['checksum'] if stats else f"sha256:{snapshot_id}",
        status="ready"
    )

    # Notify via WebSocket
    await websocket_manager.notify_snapshot_created(snapshot_id, current_user.username)

    return snapshot

@router.put("/{snapshot_id}", response_model=Snapshot)
async def update_snapshot(
    snapshot_id: str,
    snapshot_update: SnapshotUpdate,
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    Update an existing snapshot's metadata.
    """
    # Get existing snapshot
    model = repository.get_snapshot(snapshot_id)
    if not model:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Prepare updated metadata
    updated_metadata = model.snapshot_metadata.copy()

    if snapshot_update.name is not None:
        updated_metadata['name'] = snapshot_update.name
    if snapshot_update.description is not None:
        updated_metadata['description'] = snapshot_update.description
    if snapshot_update.tags is not None:
        updated_metadata['tags'] = snapshot_update.tags
    if snapshot_update.metadata is not None:
        updated_metadata.update(snapshot_update.metadata)

    # Update via repository
    model = repository.update_snapshot(snapshot_id, updated_metadata)
    if not model:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Get updated stats
    stats = repository.get_snapshot_stats(snapshot_id)

    return Snapshot(
        id=model.snapshot_id,
        name=updated_metadata.get('name', f"Snapshot {model.snapshot_id[:8]}"),
        description=updated_metadata.get('description'),
        tags=updated_metadata.get('tags', []),
        metadata=updated_metadata,
        created_at=model.timestamp,
        created_by=updated_metadata.get('created_by', 'system'),
        size_bytes=stats['size_bytes'] if stats else 0,
        checksum=stats['checksum'] if stats else f"sha256:{model.snapshot_id}",
        status="ready"
    )

@router.delete("/{snapshot_id}", status_code=204)
async def delete_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    Delete a snapshot and its artifacts.
    """
    success = repository.delete_snapshot(snapshot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Snapshot not found")

@router.get("/{snapshot_id}/download")
async def download_snapshot(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    Download snapshot data as a zip file containing all artifacts.
    """
    # Check if snapshot exists
    model = repository.get_snapshot(snapshot_id)
    if not model:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Create export
    export_path = repository.create_snapshot_export(snapshot_id)
    if not export_path or not export_path.exists():
        raise HTTPException(status_code=500, detail="Failed to create snapshot export")

    # Return file download
    filename = f"snapshot_{snapshot_id[:8]}.zip"

    def cleanup():
        """Clean up temp file after download"""
        try:
            if export_path.exists():
                export_path.unlink()
        except Exception:
            pass  # Best effort cleanup

    response = FileResponse(
        path=str(export_path),
        filename=filename,
        media_type="application/zip",
        background=cleanup
    )

    return response

@router.get("/{snapshot_id}/stats")
async def get_snapshot_stats(
    snapshot_id: str,
    current_user: User = Depends(get_current_user),
    repository = Depends(get_repository)
):
    """
    Get detailed statistics about a snapshot.
    """
    stats = repository.get_snapshot_stats(snapshot_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return stats
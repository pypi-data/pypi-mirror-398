"""Database models for Briefcase storage layer."""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, Boolean, Float,
    LargeBinary, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Snapshot(Base):
    """Immutable decision snapshot record."""

    __tablename__ = "snapshots"
    __table_args__ = (
        Index("ix_snapshots_timestamp", "timestamp"),
        Index("ix_snapshots_model_name", "model_name"),
        Index("ix_snapshots_model_version", "model_version"),
        Index("ix_snapshots_session_timestamp", "session_id", "timestamp"),
    )

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(64), nullable=False, unique=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Model information
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(64), nullable=False)
    model_config_hash = Column(String(64), nullable=True, index=True)

    # Decision context
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=False)
    snapshot_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    artifacts = relationship("Artifact", back_populates="snapshot", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Snapshot(id={self.snapshot_id}, session={self.session_id}, "
            f"model={self.model_name}:{self.model_version})>"
        )

    @validates('input_data', 'output_data', 'snapshot_metadata')
    def validate_json_fields(self, key: str, value: Any) -> Any:
        """Ensure JSON fields are serializable."""
        if value is None:
            return {} if key == 'snapshot_metadata' else None
        try:
            # Test serialization
            json.dumps(value)
            return value
        except (TypeError, ValueError) as e:
            raise ValueError(f"Field {key} must be JSON serializable: {e}")


class Artifact(Base):
    """Artifact storage record with deduplication."""

    __tablename__ = "artifacts"
    __table_args__ = (
        Index("ix_artifacts_artifact_type", "artifact_type"),
        Index("ix_artifacts_snapshot_id", "snapshot_id"),
        UniqueConstraint("snapshot_id", "artifact_name", name="uq_snapshot_artifact"),
    )

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(64), ForeignKey("snapshots.snapshot_id"), nullable=False)
    artifact_name = Column(String(255), nullable=False)
    artifact_type = Column(String(64), nullable=False)  # 'model_weights', 'config', 'metrics', etc.

    # Content tracking
    content_hash = Column(String(64), nullable=False, index=True)
    content_size = Column(Integer, nullable=False)
    content_path = Column(String(512), nullable=True)  # Path to file storage
    content_data = Column(LargeBinary, nullable=True)  # Direct blob storage

    # Compression info
    compression_type = Column(String(16), nullable=False, default="none")
    compressed_size = Column(Integer, nullable=True)  # Size after compression
    compression_ratio = Column(Float, nullable=True)

    # Metadata
    artifact_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    is_external = Column(Boolean, nullable=False, default=False)

    # Relationships
    snapshot = relationship("Snapshot", back_populates="artifacts")

    def __repr__(self) -> str:
        return (
            f"<Artifact(name={self.artifact_name}, type={self.artifact_type}, "
            f"hash={self.content_hash[:8]}, size={self.content_size})>"
        )

    @hybrid_property
    def has_content(self) -> bool:
        """Check if artifact has content stored."""
        return self.content_data is not None or self.content_path is not None

    @validates('artifact_metadata')
    def validate_metadata(self, key: str, value: Any) -> Any:
        """Ensure metadata is JSON serializable."""
        if value is None:
            return {}
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError) as e:
            raise ValueError(f"Metadata must be JSON serializable: {e}")


class ArtifactContent(Base):
    """Deduplicated artifact content storage."""

    __tablename__ = "artifact_contents"
    __table_args__ = (
        Index("ix_artifact_contents_hash", "content_hash"),
        Index("ix_artifact_contents_size", "content_size"),
    )

    # Primary fields
    content_hash = Column(String(64), primary_key=True)
    content_size = Column(Integer, nullable=False)  # Original size
    content_type = Column(String(128), nullable=True)

    # Storage options
    content_data = Column(LargeBinary, nullable=True)  # For small artifacts
    file_path = Column(String(512), nullable=True)    # For large artifacts

    # Compression info
    compression_type = Column(String(16), nullable=False, default="none")
    compressed_size = Column(Integer, nullable=True)  # Size after compression
    compression_ratio = Column(Float, nullable=True)

    # Tracking
    reference_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    last_accessed = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    def __repr__(self) -> str:
        return (
            f"<ArtifactContent(hash={self.content_hash[:8]}, "
            f"size={self.content_size}, refs={self.reference_count})>"
        )

    @hybrid_property
    def has_content(self) -> bool:
        """Check if content is available."""
        return self.content_data is not None or self.file_path is not None


class Session(Base):
    """Session tracking for grouping related snapshots."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_created_at", "created_at"),
        Index("ix_sessions_updated_at", "updated_at"),
    )

    # Primary fields
    session_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Metadata
    session_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Statistics (computed fields)
    snapshot_count = Column(Integer, nullable=False, default=0)
    total_size = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return (
            f"<Session(id={self.session_id}, name={self.name}, "
            f"snapshots={self.snapshot_count})>"
        )

    @validates('session_metadata')
    def validate_metadata(self, key: str, value: Any) -> Any:
        """Ensure metadata is JSON serializable."""
        if value is None:
            return {}
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError) as e:
            raise ValueError(f"Metadata must be JSON serializable: {e}")


class ReplayIndex(Base):
    """Index for efficient replay queries."""

    __tablename__ = "replay_index"
    __table_args__ = (
        Index("ix_replay_model_time", "model_name", "model_version", "timestamp"),
        Index("ix_replay_session_time", "session_id", "timestamp"),
        Index("ix_replay_input_hash", "input_hash"),
    )

    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_id = Column(String(64), ForeignKey("snapshots.snapshot_id"), nullable=False)
    session_id = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)

    # Indexing fields
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(64), nullable=False)
    input_hash = Column(String(64), nullable=False)
    output_hash = Column(String(64), nullable=False)

    # Quick access metadata
    has_artifacts = Column(Boolean, nullable=False, default=False)
    artifact_count = Column(Integer, nullable=False, default=0)
    total_artifact_size = Column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return (
            f"<ReplayIndex(snapshot={self.snapshot_id}, "
            f"model={self.model_name}:{self.model_version})>"
        )

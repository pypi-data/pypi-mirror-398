"""Repository for snapshot operations with SQLAlchemy integration."""

import hashlib
import json
import zipfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, BinaryIO
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc

from .database import get_session, session_scope
from .models import Snapshot as SnapshotModel, Artifact, Session as SessionModel
from .artifacts import ArtifactManager
from .encryption import EncryptionManager, EncryptionConfig, get_encryption_manager


class SnapshotRepository:
    """Repository for managing snapshots with proper database integration."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session
        self.artifact_manager = ArtifactManager(session=session)
        self.encryption_manager = get_encryption_manager()

    def _get_session(self) -> Session:
        """Get session, either provided or create new one."""
        return self._session or get_session()

    def _decrypt_snapshot_data(self, snapshot: SnapshotModel) -> SnapshotModel:
        """Decrypt sensitive data in snapshot if encryption is enabled."""
        if self.encryption_manager:
            try:
                # Create a copy to avoid modifying the original
                decrypted_input = self.encryption_manager.decrypt_data(snapshot.input_data)
                decrypted_output = self.encryption_manager.decrypt_data(snapshot.output_data)
                decrypted_metadata = self.encryption_manager.decrypt_data(snapshot.snapshot_metadata)

                # Update the snapshot object
                snapshot.input_data = decrypted_input
                snapshot.output_data = decrypted_output
                snapshot.snapshot_metadata = decrypted_metadata
            except Exception:
                # If decryption fails, return data as-is (might be unencrypted)
                pass

        return snapshot

    def create_snapshot(
        self,
        name: str,
        description: Optional[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        created_by: str = "system",
        session_id: Optional[str] = None,
        model_name: str = "unknown",
        model_version: str = "1.0",
        input_data: Dict[str, Any] = None,
        output_data: Dict[str, Any] = None,
    ) -> SnapshotModel:
        """Create a new snapshot with proper state capture."""
        snapshot_id = str(uuid4())

        # Generate session_id if not provided
        if session_id is None:
            session_id = str(uuid4())

        # Prepare data
        input_data = input_data or {}
        output_data = output_data or {}
        metadata = metadata or {}
        tags = tags or []

        # Encrypt sensitive data if encryption is enabled
        if self.encryption_manager:
            input_data = self.encryption_manager.encrypt_data(input_data)
            output_data = self.encryption_manager.encrypt_data(output_data)
            metadata = self.encryption_manager.encrypt_data(metadata)

        # Calculate content hash for model config
        model_config = {
            "model_name": model_name,
            "model_version": model_version,
            "metadata": metadata
        }
        model_config_hash = hashlib.sha256(
            json.dumps(model_config, sort_keys=True).encode()
        ).hexdigest()

        session = self._get_session()
        try:
            # Create snapshot record
            snapshot = SnapshotModel(
                snapshot_id=snapshot_id,
                session_id=session_id,
                model_name=model_name,
                model_version=model_version,
                model_config_hash=model_config_hash,
                input_data=input_data,
                output_data=output_data,
                snapshot_metadata=metadata,
                timestamp=datetime.now(timezone.utc),
            )

            session.add(snapshot)

            # Create or update session record
            session_record = session.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()

            if session_record is None:
                session_record = SessionModel(
                    session_id=session_id,
                    name=f"Session {session_id[:8]}",
                    description="Auto-created session",
                    session_metadata={"created_by": created_by},
                    snapshot_count=1,
                    total_size=0,
                )
                session.add(session_record)
            else:
                session_record.snapshot_count += 1
                session_record.updated_at = datetime.now(timezone.utc)

            # Store metadata as artifact if provided
            if metadata:
                self.artifact_manager.store_artifact(
                    snapshot_id=snapshot_id,
                    name="snapshot_metadata.json",
                    content=json.dumps(metadata, indent=2),
                    artifact_type="metadata",
                    content_type="application/json",
                )

            # Store input/output data as artifacts for large payloads
            if input_data:
                self.artifact_manager.store_artifact(
                    snapshot_id=snapshot_id,
                    name="input_data.json",
                    content=json.dumps(input_data, indent=2),
                    artifact_type="input",
                    content_type="application/json",
                )

            if output_data:
                self.artifact_manager.store_artifact(
                    snapshot_id=snapshot_id,
                    name="output_data.json",
                    content=json.dumps(output_data, indent=2),
                    artifact_type="output",
                    content_type="application/json",
                )

            # Always commit for create operations
            session.commit()

            return snapshot

        except Exception as e:
            session.rollback()
            raise
        finally:
            # Don't close session if it was provided externally
            if self._session is None:
                session.close()

    def get_snapshot(self, snapshot_id: str) -> Optional[SnapshotModel]:
        """Get a snapshot by ID."""
        session = self._get_session()
        try:
            snapshot = session.query(SnapshotModel).filter(
                SnapshotModel.snapshot_id == snapshot_id
            ).first()

            if snapshot:
                snapshot = self._decrypt_snapshot_data(snapshot)

            return snapshot
        finally:
            if self._session is None:
                session.close()

    def list_snapshots(
        self,
        skip: int = 0,
        limit: int = 100,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> List[SnapshotModel]:
        """List snapshots with filtering and pagination."""
        session = self._get_session()
        try:
            query = session.query(SnapshotModel)

            # Apply filters
            if session_id:
                query = query.filter(SnapshotModel.session_id == session_id)

            if model_name:
                query = query.filter(SnapshotModel.model_name == model_name)

            # Order by timestamp (newest first)
            query = query.order_by(desc(SnapshotModel.timestamp))

            # Apply pagination
            snapshots = query.offset(skip).limit(limit).all()

            # Decrypt sensitive data
            return [self._decrypt_snapshot_data(snapshot) for snapshot in snapshots]

        finally:
            if self._session is None:
                session.close()

    def update_snapshot(
        self,
        snapshot_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SnapshotModel]:
        """Update snapshot metadata."""
        session = self._get_session()
        try:
            snapshot = session.query(SnapshotModel).filter(
                SnapshotModel.snapshot_id == snapshot_id
            ).first()

            if not snapshot:
                return None

            if metadata is not None:
                snapshot.snapshot_metadata = metadata

                # Update metadata artifact
                self.artifact_manager.store_artifact(
                    snapshot_id=snapshot_id,
                    name="snapshot_metadata.json",
                    content=json.dumps(metadata, indent=2),
                    artifact_type="metadata",
                    content_type="application/json",
                )

            if self._session is None:
                session.commit()

            return snapshot

        except Exception as e:
            if self._session is None:
                session.rollback()
            raise
        finally:
            if self._session is None:
                session.close()

    def delete_snapshot(self, snapshot_id: str) -> bool:
        """Delete a snapshot and its artifacts."""
        session = self._get_session()
        try:
            snapshot = session.query(SnapshotModel).filter(
                SnapshotModel.snapshot_id == snapshot_id
            ).first()

            if not snapshot:
                return False

            # Delete associated artifacts
            artifacts = self.artifact_manager.get_artifacts(snapshot_id)
            for artifact in artifacts:
                self.artifact_manager.delete_artifact(snapshot_id, artifact.artifact_name)

            # Update session counts
            session_record = session.query(SessionModel).filter(
                SessionModel.session_id == snapshot.session_id
            ).first()

            if session_record:
                session_record.snapshot_count = max(0, session_record.snapshot_count - 1)
                session_record.updated_at = datetime.now(timezone.utc)

            # Delete snapshot
            session.delete(snapshot)

            if self._session is None:
                session.commit()

            return True

        except Exception as e:
            if self._session is None:
                session.rollback()
            raise
        finally:
            if self._session is None:
                session.close()

    def get_snapshot_stats(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics about a snapshot."""
        session = self._get_session()
        try:
            snapshot = session.query(SnapshotModel).filter(
                SnapshotModel.snapshot_id == snapshot_id
            ).first()

            if not snapshot:
                return None

            # Get artifacts
            artifacts = self.artifact_manager.get_artifacts(snapshot_id)

            total_size = sum(artifact.content_size for artifact in artifacts)
            artifact_count = len(artifacts)

            # Group by type
            artifact_types = {}
            for artifact in artifacts:
                artifact_types[artifact.artifact_type] = artifact_types.get(artifact.artifact_type, 0) + 1

            # Calculate checksum from snapshot data
            content_for_hash = {
                "input_data": snapshot.input_data,
                "output_data": snapshot.output_data,
                "metadata": snapshot.snapshot_metadata,
                "model_config_hash": snapshot.model_config_hash,
            }
            checksum = hashlib.sha256(
                json.dumps(content_for_hash, sort_keys=True).encode()
            ).hexdigest()

            return {
                "id": snapshot.snapshot_id,
                "size_bytes": total_size,
                "checksum": f"sha256:{checksum}",
                "compression_ratio": 1.0,  # TODO: Implement compression
                "file_count": artifact_count,
                "artifact_types": artifact_types,
                "created_at": snapshot.timestamp,
                "age_seconds": (datetime.now(timezone.utc) - (snapshot.timestamp.replace(tzinfo=timezone.utc) if snapshot.timestamp.tzinfo is None else snapshot.timestamp)).total_seconds(),
                "model_name": snapshot.model_name,
                "model_version": snapshot.model_version,
            }

        finally:
            if self._session is None:
                session.close()

    def create_snapshot_export(self, snapshot_id: str) -> Optional[Path]:
        """Create a zip export of a snapshot with all its artifacts."""
        session = self._get_session()
        try:
            snapshot = session.query(SnapshotModel).filter(
                SnapshotModel.snapshot_id == snapshot_id
            ).first()

            if not snapshot:
                return None

            # Create temporary zip file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f"_{snapshot_id[:8]}.zip",
                delete=False
            )
            temp_path = Path(temp_file.name)
            temp_file.close()

            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add snapshot metadata
                snapshot_info = {
                    "id": snapshot.snapshot_id,
                    "session_id": snapshot.session_id,
                    "model_name": snapshot.model_name,
                    "model_version": snapshot.model_version,
                    "timestamp": snapshot.timestamp.isoformat(),
                    "input_data": snapshot.input_data,
                    "output_data": snapshot.output_data,
                    "metadata": snapshot.snapshot_metadata,
                }

                zipf.writestr(
                    "snapshot_info.json",
                    json.dumps(snapshot_info, indent=2)
                )

                # Add artifacts
                artifacts = self.artifact_manager.get_artifacts(snapshot_id)
                for artifact in artifacts:
                    try:
                        content = self.artifact_manager.get_artifact_content(artifact)
                        artifact_path = f"artifacts/{artifact.artifact_name}"
                        zipf.writestr(artifact_path, content)

                        # Add artifact metadata
                        artifact_info = {
                            "name": artifact.artifact_name,
                            "type": artifact.artifact_type,
                            "size": artifact.content_size,
                            "hash": artifact.content_hash,
                            "metadata": artifact.artifact_metadata,
                            "created_at": artifact.created_at.isoformat(),
                        }
                        zipf.writestr(
                            f"artifacts/{artifact.artifact_name}.meta.json",
                            json.dumps(artifact_info, indent=2)
                        )
                    except Exception as e:
                        # Log error but continue with other artifacts
                        print(f"Warning: Could not export artifact {artifact.artifact_name}: {e}")

            return temp_path

        finally:
            if self._session is None:
                session.close()

    def get_repository_stats(self) -> Dict[str, Any]:
        """Get overall repository statistics."""
        session = self._get_session()
        try:
            # Snapshot counts
            total_snapshots = session.query(func.count(SnapshotModel.id)).scalar()

            # Session counts
            total_sessions = session.query(func.count(SessionModel.session_id)).scalar()

            # Model distribution
            model_counts = dict(
                session.query(SnapshotModel.model_name, func.count(SnapshotModel.id))
                .group_by(SnapshotModel.model_name)
                .all()
            )

            # Recent activity
            recent_snapshots = session.query(func.count(SnapshotModel.id)).filter(
                SnapshotModel.timestamp >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            ).scalar()

            # Storage stats
            storage_stats = self.artifact_manager.get_storage_stats()

            return {
                "total_snapshots": total_snapshots,
                "total_sessions": total_sessions,
                "model_distribution": model_counts,
                "recent_snapshots_today": recent_snapshots,
                "storage": storage_stats,
            }

        finally:
            if self._session is None:
                session.close()


def get_snapshot_repository(session: Optional[Session] = None) -> SnapshotRepository:
    """Get a configured snapshot repository instance."""
    return SnapshotRepository(session=session)
"""Repository pattern for storage operations and queries."""

import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from .database import get_session, session_scope


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)
from .models import Snapshot, Artifact, Session as SessionModel, ReplayIndex


class SnapshotRepository:
    """Repository for snapshot storage and retrieval operations."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def _get_session(self) -> Session:
        """Get session, either provided or create new one."""
        return self._session or get_session()

    def create_snapshot(
        self,
        snapshot_id: str,
        session_id: str,
        model_name: str,
        model_version: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        model_config_hash: Optional[str] = None,
    ) -> Snapshot:
        """Create a new immutable snapshot record."""
        session = self._get_session()

        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            session_id=session_id,
            model_name=model_name,
            model_version=model_version,
            input_data=input_data,
            output_data=output_data,
            snapshot_metadata=metadata or {},
            model_config_hash=model_config_hash,
        )

        try:
            session.add(snapshot)
            if self._session is None:
                session.commit()

            # Create replay index entry
            self._create_replay_index_entry(snapshot, session)

            return snapshot
        except IntegrityError as e:
            if self._session is None:
                session.rollback()
            raise ValueError(f"Snapshot with ID {snapshot_id} already exists") from e
        finally:
            if self._session is None:
                session.close()

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Retrieve snapshot by ID with artifacts preloaded."""
        session = self._get_session()
        try:
            return (
                session.query(Snapshot)
                .options(joinedload(Snapshot.artifacts))
                .filter(Snapshot.snapshot_id == snapshot_id)
                .first()
            )
        finally:
            if self._session is None:
                session.close()

    def get_snapshots_by_session(
        self, session_id: str, limit: int = 100, offset: int = 0
    ) -> List[Snapshot]:
        """Get snapshots for a session, ordered by timestamp."""
        session = self._get_session()
        try:
            return (
                session.query(Snapshot)
                .filter(Snapshot.session_id == session_id)
                .order_by(desc(Snapshot.timestamp))
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def get_snapshots_by_model(
        self,
        model_name: str,
        model_version: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Snapshot]:
        """Get snapshots for a specific model version."""
        session = self._get_session()
        try:
            query = session.query(Snapshot).filter(Snapshot.model_name == model_name)

            if model_version:
                query = query.filter(Snapshot.model_version == model_version)

            return (
                query.order_by(desc(Snapshot.timestamp))
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def search_snapshots(
        self,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        model_version: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Snapshot]:
        """Advanced snapshot search with multiple filters."""
        session = self._get_session()
        try:
            query = session.query(Snapshot)

            # Apply filters
            if session_id:
                query = query.filter(Snapshot.session_id == session_id)
            if model_name:
                query = query.filter(Snapshot.model_name == model_name)
            if model_version:
                query = query.filter(Snapshot.model_version == model_version)
            if start_time:
                query = query.filter(Snapshot.timestamp >= start_time)
            if end_time:
                query = query.filter(Snapshot.timestamp <= end_time)

            # Metadata filters (JSON queries)
            if metadata_filters:
                for key, value in metadata_filters.items():
                    query = query.filter(
                        func.json_extract(Snapshot.snapshot_metadata, f'$.{key}') == value
                    )

            return (
                query.order_by(desc(Snapshot.timestamp))
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def count_snapshots(self, session_id: Optional[str] = None) -> int:
        """Count total snapshots, optionally filtered by session."""
        session = self._get_session()
        try:
            query = session.query(func.count(Snapshot.id))
            if session_id:
                query = query.filter(Snapshot.session_id == session_id)
            return query.scalar()
        finally:
            if self._session is None:
                session.close()

    def _create_replay_index_entry(self, snapshot: Snapshot, session: Session) -> None:
        """Create replay index entry for efficient queries."""
        input_hash = self._compute_hash(snapshot.input_data)
        output_hash = self._compute_hash(snapshot.output_data)

        index_entry = ReplayIndex(
            snapshot_id=snapshot.snapshot_id,
            session_id=snapshot.session_id,
            timestamp=snapshot.timestamp,
            model_name=snapshot.model_name,
            model_version=snapshot.model_version,
            input_hash=input_hash,
            output_hash=output_hash,
        )

        session.add(index_entry)

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        """Compute deterministic hash of data."""
        import json
        serialized = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode()).hexdigest()


class SessionRepository:
    """Repository for session management."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def _get_session(self) -> Session:
        """Get session, either provided or create new one."""
        return self._session or get_session()

    def create_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionModel:
        """Create a new session."""
        session = self._get_session()

        session_model = SessionModel(
            session_id=session_id,
            name=name,
            description=description,
            session_metadata=metadata or {},
        )

        try:
            session.add(session_model)
            if self._session is None:
                session.commit()
            return session_model
        except IntegrityError as e:
            if self._session is None:
                session.rollback()
            raise ValueError(f"Session with ID {session_id} already exists") from e
        finally:
            if self._session is None:
                session.close()

    def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Get session by ID."""
        session = self._get_session()
        try:
            return session.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()
        finally:
            if self._session is None:
                session.close()

    def update_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SessionModel]:
        """Update session metadata."""
        session = self._get_session()
        try:
            session_model = session.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()

            if not session_model:
                return None

            if name is not None:
                session_model.name = name
            if description is not None:
                session_model.description = description
            if metadata is not None:
                session_model.session_metadata = metadata

            session_model.updated_at = _utcnow()

            if self._session is None:
                session.commit()
            return session_model
        finally:
            if self._session is None:
                session.close()

    def list_sessions(self, limit: int = 100, offset: int = 0) -> List[SessionModel]:
        """List all sessions ordered by updated date."""
        session = self._get_session()
        try:
            return (
                session.query(SessionModel)
                .order_by(desc(SessionModel.updated_at))
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def update_session_stats(self, session_id: str) -> None:
        """Update session statistics (snapshot count, total size)."""
        session = self._get_session()
        try:
            # Get snapshot count
            snapshot_count = (
                session.query(func.count(Snapshot.id))
                .filter(Snapshot.session_id == session_id)
                .scalar()
            )

            # Calculate total size from artifacts
            total_size = (
                session.query(func.coalesce(func.sum(Artifact.content_size), 0))
                .join(Snapshot, Snapshot.snapshot_id == Artifact.snapshot_id)
                .filter(Snapshot.session_id == session_id)
                .scalar()
            )

            # Update session model
            session_model = session.query(SessionModel).filter(
                SessionModel.session_id == session_id
            ).first()

            if session_model:
                session_model.snapshot_count = snapshot_count
                session_model.total_size = total_size
                session_model.updated_at = _utcnow()

                if self._session is None:
                    session.commit()
        finally:
            if self._session is None:
                session.close()


class ReplayRepository:
    """Repository for replay operations and queries."""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    def _get_session(self) -> Session:
        """Get session, either provided or create new one."""
        return self._session or get_session()

    def find_similar_snapshots(
        self,
        input_hash: str,
        model_name: str,
        model_version: Optional[str] = None,
        limit: int = 10,
    ) -> List[ReplayIndex]:
        """Find snapshots with similar inputs for replay scenarios."""
        session = self._get_session()
        try:
            query = (
                session.query(ReplayIndex)
                .filter(
                    and_(
                        ReplayIndex.input_hash == input_hash,
                        ReplayIndex.model_name == model_name
                    )
                )
            )

            if model_version:
                query = query.filter(ReplayIndex.model_version == model_version)

            return (
                query.order_by(desc(ReplayIndex.timestamp))
                .limit(limit)
                .all()
            )
        finally:
            if self._session is None:
                session.close()

    def get_replay_timeline(
        self,
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[ReplayIndex]:
        """Get chronological replay timeline for a session."""
        session = self._get_session()
        try:
            query = session.query(ReplayIndex).filter(
                ReplayIndex.session_id == session_id
            )

            if start_time:
                query = query.filter(ReplayIndex.timestamp >= start_time)
            if end_time:
                query = query.filter(ReplayIndex.timestamp <= end_time)

            return query.order_by(ReplayIndex.timestamp).all()
        finally:
            if self._session is None:
                session.close()

    def get_model_evolution(
        self,
        model_name: str,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Tuple[str, int, datetime]]:
        """Get model version evolution over time."""
        session = self._get_session()
        try:
            query = (
                session.query(
                    ReplayIndex.model_version,
                    func.count(ReplayIndex.id),
                    func.min(ReplayIndex.timestamp),
                )
                .filter(ReplayIndex.model_name == model_name)
                .group_by(ReplayIndex.model_version)
            )

            if session_id:
                query = query.filter(ReplayIndex.session_id == session_id)

            return (
                query.order_by(func.min(ReplayIndex.timestamp))
                .limit(limit)
                .all()
            )
        finally:
            if self._session is None:
                session.close()

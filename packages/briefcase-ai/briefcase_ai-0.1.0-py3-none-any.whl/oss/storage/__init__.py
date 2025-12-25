"""Briefcase Storage Layer - Immutable snapshots and artifact management."""

from .database import (
    DatabaseConfig,
    DatabaseManager,
    get_database_manager,
    configure_database,
    get_session,
    session_scope,
    init_database,
    reset_database,
    Base,
)

from .models import (
    Snapshot,
    Artifact,
    ArtifactContent,
    Session,
    ReplayIndex,
)

from .repository import (
    SnapshotRepository,
    SessionRepository,
    ReplayRepository,
)

from .artifacts import (
    ArtifactManager,
    get_artifact_manager,
)

__version__ = "0.1.0"

__all__ = [
    # Database
    "DatabaseConfig",
    "DatabaseManager",
    "get_database_manager",
    "configure_database",
    "get_session",
    "session_scope",
    "init_database",
    "reset_database",
    "Base",

    # Models
    "Snapshot",
    "Artifact",
    "ArtifactContent",
    "Session",
    "ReplayIndex",

    # Repositories
    "SnapshotRepository",
    "SessionRepository",
    "ReplayRepository",

    # Artifact Management
    "ArtifactManager",
    "get_artifact_manager",
]


def setup_storage(database_url: str = None, echo: bool = False) -> None:
    """Initialize storage with configuration."""
    config = DatabaseConfig(url=database_url, echo=echo)
    configure_database(config)
    init_database()


def create_session_with_snapshots(
    session_id: str,
    session_name: str = None,
    session_description: str = None,
    session_metadata: dict = None,
) -> tuple[SessionRepository, SnapshotRepository, ArtifactManager]:
    """Convenience function to create coordinated storage services for a session."""
    with session_scope() as db_session:
        session_repo = SessionRepository(db_session)
        snapshot_repo = SnapshotRepository(db_session)
        artifact_manager = ArtifactManager(session=db_session)

        # Create session if it doesn't exist
        existing_session = session_repo.get_session(session_id)
        if not existing_session:
            session_repo.create_session(
                session_id=session_id,
                name=session_name,
                description=session_description,
                metadata=session_metadata or {},
            )

        return session_repo, snapshot_repo, artifact_manager
"""Database configuration and session management for Briefcase storage."""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Base class for all ORM models
Base = declarative_base()

# Database configuration
DEFAULT_DATABASE_URL = "sqlite:///./briefcase.db"


class DatabaseConfig:
    """Configuration for database connections."""

    def __init__(
        self,
        url: Optional[str] = None,
        echo: bool = False,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600,
    ):
        self.url = url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        self.echo = echo
        self.pool_pre_ping = pool_pre_ping
        self.pool_recycle = pool_recycle

    @property
    def is_sqlite(self) -> bool:
        """Check if the configured database is SQLite."""
        return self.url.startswith("sqlite:")


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def engine(self) -> Engine:
        """Get or create the database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        return self._session_factory

    def _create_engine(self) -> Engine:
        """Create the SQLAlchemy engine with appropriate configuration."""
        engine_kwargs = {
            "echo": self.config.echo,
            "pool_pre_ping": self.config.pool_pre_ping,
        }

        # SQLite-specific configuration
        if self.config.is_sqlite:
            # Enable WAL mode for better concurrency
            engine_kwargs.update({
                "connect_args": {
                    "check_same_thread": False,
                },
                "poolclass": StaticPool,
            })
        else:
            engine_kwargs["pool_recycle"] = self.config.pool_recycle

        return create_engine(self.config.url, **engine_kwargs)

    def create_tables(self) -> None:
        """Create all tables defined in the models."""
        Base.metadata.create_all(bind=self.engine)

    def drop_tables(self) -> None:
        """Drop all tables (useful for testing)."""
        Base.metadata.drop_all(bind=self.engine)

    def get_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def configure_database(config: DatabaseConfig) -> None:
    """Configure the global database manager with custom settings."""
    global _db_manager
    _db_manager = DatabaseManager(config)


def get_session() -> Session:
    """Get a new database session using the global manager."""
    return get_database_manager().get_session()


def session_scope() -> Generator[Session, None, None]:
    """Get a transactional session scope using the global manager."""
    yield from get_database_manager().session_scope()


def init_database() -> None:
    """Initialize the database by creating all tables."""
    # Import models to ensure they're registered with Base
    from . import models  # noqa
    get_database_manager().create_tables()


def reset_database() -> None:
    """Reset the database by dropping and recreating all tables."""
    from . import models  # noqa
    manager = get_database_manager()
    manager.drop_tables()
    manager.create_tables()

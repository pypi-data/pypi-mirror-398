"""Base database plugin interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator

from sqlalchemy import Engine, MetaData
from sqlalchemy.orm import Session, declarative_base

if TYPE_CHECKING:
    from sonnerrise_core.config import DatabaseConfig

# Shared SQLAlchemy base for all models
Base = declarative_base()
metadata: MetaData = Base.metadata


class DatabaseSession:
    """Wrapper around SQLAlchemy session with context manager support."""

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        """Get the underlying SQLAlchemy session."""
        return self._session

    def add(self, instance: Any) -> None:
        """Add an instance to the session."""
        self._session.add(instance)

    def add_all(self, instances: list[Any]) -> None:
        """Add multiple instances to the session."""
        self._session.add_all(instances)

    def delete(self, instance: Any) -> None:
        """Mark an instance for deletion."""
        self._session.delete(instance)

    def commit(self) -> None:
        """Commit the current transaction."""
        self._session.commit()

    def rollback(self) -> None:
        """Rollback the current transaction."""
        self._session.rollback()

    def flush(self) -> None:
        """Flush pending changes to the database."""
        self._session.flush()

    def refresh(self, instance: Any) -> None:
        """Refresh an instance from the database."""
        self._session.refresh(instance)

    def query(self, *entities: Any) -> Any:
        """Create a query for the given entities."""
        return self._session.query(*entities)

    def execute(self, statement: Any) -> Any:
        """Execute a SQL statement."""
        return self._session.execute(statement)

    def close(self) -> None:
        """Close the session."""
        self._session.close()


class DatabasePlugin(ABC):
    """Abstract base class for database plugins.

    Plugins implement this interface to provide database connectivity
    for different database engines (MySQL, PostgreSQL, SQLite, etc.).
    """

    def __init__(self, config: DatabaseConfig) -> None:
        """Initialize the plugin with configuration.

        Args:
            config: Database configuration object.
        """
        self._config = config
        self._engine: Engine | None = None

    @property
    def config(self) -> DatabaseConfig:
        """Get the database configuration."""
        return self._config

    @property
    def engine(self) -> Engine:
        """Get the SQLAlchemy engine, creating it if necessary."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @abstractmethod
    def _create_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine.

        Subclasses must implement this to create an engine appropriate
        for their database backend.

        Returns:
            A configured SQLAlchemy Engine instance.
        """
        ...

    @abstractmethod
    def get_connection_url(self) -> str:
        """Get the database connection URL.

        Returns:
            A SQLAlchemy-compatible connection URL string.
        """
        ...

    def create_tables(self) -> None:
        """Create all tables defined in the metadata."""
        from sonnerrise_core.models import import_all_models
        import_all_models()
        metadata.create_all(self.engine)
    
    def drop_tables(self) -> None:
        """Drop all tables defined in the metadata."""
        metadata.drop_all(self.engine)

    @contextmanager
    def session(self) -> Generator[DatabaseSession, None, None]:
        """Create a new database session as a context manager.

        Yields:
            A DatabaseSession instance that will be automatically
            committed on success or rolled back on exception.

        Example:
            with db.session() as session:
                session.add(my_object)
                session.commit()
        """
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=self.engine)
        session = SessionLocal()
        db_session = DatabaseSession(session)

        try:
            yield db_session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self) -> DatabaseSession:
        """Create a new database session.

        Returns:
            A DatabaseSession instance. Caller is responsible for
            committing/rolling back and closing the session.
        """
        from sqlalchemy.orm import sessionmaker

        SessionLocal = sessionmaker(bind=self.engine)
        return DatabaseSession(SessionLocal())

    def test_connection(self) -> bool:
        """Test the database connection.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(self._get_test_query())
            return True
        except Exception:
            return False

    def _get_test_query(self) -> Any:
        """Get a simple query to test the connection."""
        from sqlalchemy import text

        return text("SELECT 1")

    def close(self) -> None:
        """Close the database connection and dispose of the engine."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

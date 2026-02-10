"""
Database Connection and Session Management

Provides SQLAlchemy engine and session management for the Pipeline system.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session, sessionmaker

import config
from src.db.models import Base


# Global engine and session maker
_engine: Engine | None = None
_session_maker: sessionmaker | None = None


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.

    Returns:
        Engine: SQLAlchemy engine instance
    """
    global _engine

    if _engine is None:
        # Ensure base pipelines directory exists
        base_path = Path(config.BASE_PIPELINES_PATH)
        base_path.mkdir(parents=True, exist_ok=True)

        # For now, we'll use a centralized database for pipeline metadata
        # Individual pipeline databases will be created per pipeline
        db_path = base_path / "pipeline_system.db"

        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,  # Set to True for SQL query logging
            connect_args={"check_same_thread": False},  # Needed for SQLite
            pool_pre_ping=True,  # Verify connections before using
        )

    return _engine


def get_session_maker() -> sessionmaker:
    """
    Get or create the session maker.

    Returns:
        sessionmaker: SQLAlchemy session maker
    """
    global _session_maker

    if _session_maker is None:
        engine = get_engine()
        _session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

    return _session_maker


def init_system_db() -> None:
    """
    Initialize the system database by creating all tables.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """
    Get a new database session.

    Returns:
        Session: SQLAlchemy session
    """
    session_maker = get_session_maker()
    return session_maker()


@contextmanager
def get_db_session_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Automatically commits or rolls back transactions and closes the session.

    Yields:
        Session: SQLAlchemy session

    Example:
        ```python
        with get_db_session_context() as session:
            pipeline = session.query(Pipeline).first()
            print(pipeline.pipeline_name)
        ```
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Alias for backwards compatibility
get_db_session = get_db_session_context


def get_db() -> Iterator[Session]:
    """
    FastAPI dependency for database sessions.

    Yields a session and handles cleanup after request.

    Yields:
        Session: SQLAlchemy session
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_pipeline_db_path(pipeline_id: str) -> Path:
    """
    Get the database path for a specific pipeline.

    Args:
        pipeline_id: The pipeline UUID

    Returns:
        Path: Path to the pipeline's database file
    """
    pipeline_path = Path(config.BASE_PIPELINES_PATH) / pipeline_id
    db_dir = pipeline_path / config.PIPELINE_SYSTEM_DIR / config.PIPELINE_DB_DIR
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / config.DB_FILENAME


def get_pipeline_engine(pipeline_id: str) -> Engine:
    """
    Get or create a SQLAlchemy engine for a specific pipeline.

    Args:
        pipeline_id: The pipeline UUID

    Returns:
        Engine: SQLAlchemy engine for the pipeline
    """
    db_path = get_pipeline_db_path(pipeline_id)

    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )

    return engine


def init_pipeline_db(pipeline_id: str) -> None:
    """
    Initialize a pipeline's database by creating all tables.

    Args:
        pipeline_id: The pipeline UUID
    """
    engine = get_pipeline_engine(pipeline_id)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_pipeline_db_session(pipeline_id: str) -> Generator[Session, None, None]:
    """
    Context manager for pipeline-specific database sessions.

    Args:
        pipeline_id: The pipeline UUID

    Yields:
        Session: SQLAlchemy session for the pipeline
    """
    engine = get_pipeline_engine(pipeline_id)
    session_maker = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

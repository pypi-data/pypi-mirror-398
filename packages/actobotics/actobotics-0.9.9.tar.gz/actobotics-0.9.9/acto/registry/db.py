from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from acto.config.settings import Settings


def make_engine(settings: Settings):
    connect_args = {"check_same_thread": False} if settings.db_url.startswith("sqlite") else {}
    
    # Connection pooling only for non-SQLite databases
    pool_kwargs = {}
    if not settings.db_url.startswith("sqlite"):
        pool_kwargs = {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,  # Verify connections before using
        }
    
    engine = create_engine(settings.db_url, connect_args=connect_args, **pool_kwargs)
    
    # Enable WAL mode for SQLite for better concurrency
    if settings.db_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):  # noqa: ARG001
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    
    return engine


def make_session_factory(engine: Engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

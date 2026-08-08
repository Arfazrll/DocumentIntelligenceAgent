"""
DocIntel AI — Database Engine & Session Factory (SQLite + aiosqlite).
"""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from pathlib import Path

from app.config import settings

# Ensure parent directory for SQLite database exists
if settings.DATABASE_URL.startswith("sqlite"):
    db_file_str = settings.DATABASE_URL.split(":///")[-1]
    db_path = Path(db_file_str)
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)

class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass

# Create async engine for SQLite
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # SQLite-specific: enable WAL mode for better concurrent read performance
    connect_args={"check_same_thread": False, "timeout": 30},
)

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

# Async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    """Get an async database session (dependency injection for FastAPI)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db():
    """Initialize database — create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

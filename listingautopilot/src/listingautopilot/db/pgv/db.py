"""SQLAlchemy database setup."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from listingautopilot.config import settings
from listingautopilot.logging import get_logger


logger = get_logger(__name__)


class Base(DeclarativeBase):
    pass


def get_engine(database_url: str | None = None):
    url = database_url or settings.database_url
    if not url:
        logger.error("DATABASE_URL is not configured")
        raise RuntimeError("DATABASE_URL is not configured")
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    logger.debug("Creating SQLAlchemy engine dialect=%s", url.split(":", 1)[0])
    return create_engine(url, pool_pre_ping=True, connect_args=connect_args)


def get_sessionmaker(database_url: str | None = None) -> sessionmaker[Session]:
    engine = get_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

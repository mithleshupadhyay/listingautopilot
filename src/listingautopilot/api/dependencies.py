"""FastAPI dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from listingautopilot.core.config import settings
from listingautopilot.db.pgv.db import get_db
from listingautopilot.logging import get_logger


logger = get_logger(__name__)


def get_optional_db() -> Generator[Session | None, None, None]:
    if not settings.persistence_enabled:
        logger.debug("DATABASE_URL is not configured; yielding no DB session")
        yield None
        return

    db_gen = get_db()
    db = next(db_gen)
    try:
        logger.debug("DB session opened")
        yield db
    finally:
        db.close()
        logger.debug("DB session closed")

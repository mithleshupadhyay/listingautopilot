"""Health API."""

from fastapi import APIRouter
from listingautopilot.config import settings
from listingautopilot.logging import get_logger


router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "service": "listing-autopilot",
        "version": settings.app_version,
    }

"""Image asset router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from listingautopilot.core.config import settings
from listingautopilot.db.pgv.crud.assets import (
    get_image_asset,
    list_project_image_assets,
)
from listingautopilot.db.pgv.crud.projects import get_project
from listingautopilot.db.pgv.schemas.assets import ImageAssetOut
from listingautopilot.logging import get_logger

from .dependencies import get_optional_db


router = APIRouter(tags=["assets"])
logger = get_logger(__name__)


@router.get("/v1/projects/{project_id}/assets", response_model=list[ImageAssetOut])
def project_assets(
    project_id: UUID,
    db: Session | None = Depends(get_optional_db),
) -> list[ImageAssetOut]:
    if db is None:
        logger.warning("Project assets requested but DATABASE_URL is not configured")
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    project = get_project(
        db=db,
        id=project_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    if not project:
        logger.warning("Project assets requested for missing project_id=%s", project_id)
        raise HTTPException(status_code=404, detail="Project not found.")

    assets = list_project_image_assets(
        db=db,
        project_id=project_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    return [ImageAssetOut.model_validate(asset) for asset in assets]


@router.get("/v1/assets/{asset_id}", response_model=ImageAssetOut)
def asset_detail(
    asset_id: UUID,
    db: Session | None = Depends(get_optional_db),
) -> ImageAssetOut:
    if db is None:
        logger.warning("Asset detail requested but DATABASE_URL is not configured")
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    asset = get_image_asset(
        db=db,
        id=asset_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    if not asset:
        logger.warning("Asset detail requested for missing asset_id=%s", asset_id)
        raise HTTPException(status_code=404, detail="Image asset not found.")

    return ImageAssetOut.model_validate(asset)

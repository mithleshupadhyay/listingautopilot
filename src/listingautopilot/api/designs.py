"""Editable design router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from listingautopilot.core.config import settings
from listingautopilot.db.pgv.crud.designs import (
    get_editable_design,
    list_project_designs,
)
from listingautopilot.db.pgv.crud.projects import get_project
from listingautopilot.db.pgv.schemas.designs import EditableDesignOut
from listingautopilot.logging import get_logger

from .dependencies import get_optional_db


router = APIRouter(tags=["designs"])
logger = get_logger(__name__)


@router.get("/v1/projects/{project_id}/designs", response_model=list[EditableDesignOut])
def project_designs(
    project_id: UUID,
    db: Session | None = Depends(get_optional_db),
) -> list[EditableDesignOut]:
    if db is None:
        logger.warning("Project designs requested but DATABASE_URL is not configured")
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    project = get_project(
        db=db,
        id=project_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    if not project:
        logger.warning("Project designs requested for missing project_id=%s", project_id)
        raise HTTPException(status_code=404, detail="Project not found.")

    designs = list_project_designs(
        db=db,
        project_id=project_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    return [EditableDesignOut.model_validate(design) for design in designs]


@router.get("/v1/designs/{design_id}", response_model=EditableDesignOut)
def design_detail(
    design_id: UUID,
    db: Session | None = Depends(get_optional_db),
) -> EditableDesignOut:
    if db is None:
        logger.warning("Design detail requested but DATABASE_URL is not configured")
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    design = get_editable_design(
        db=db,
        id=design_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    if not design:
        logger.warning("Design detail requested for missing design_id=%s", design_id)
        raise HTTPException(status_code=404, detail="Editable design not found.")

    return EditableDesignOut.model_validate(design)

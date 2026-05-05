"""Project router."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from listingautopilot.core.config import settings
from listingautopilot.db.pgv.crud.projects import get_project, list_recent_projects
from listingautopilot.db.pgv.schemas.projects import ProjectOut, ProjectSummaryOut
from listingautopilot.logging import get_logger

from .dependencies import get_optional_db


router = APIRouter(prefix="/v1/projects", tags=["projects"])
logger = get_logger(__name__)


@router.get("/recent", response_model=list[ProjectSummaryOut])
def recent_projects(
    limit: int = 5,
    db: Session | None = Depends(get_optional_db),
) -> list[ProjectSummaryOut]:
    if db is None:
        logger.debug("Recent projects requested with persistence disabled")
        return []

    projects = list_recent_projects(
        db=db,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
        limit=limit,
    )
    return [ProjectSummaryOut.model_validate(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def project_detail(
    project_id: UUID,
    db: Session | None = Depends(get_optional_db),
) -> ProjectOut:
    if db is None:
        logger.warning("Project detail requested but DATABASE_URL is not configured")
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")

    project = get_project(
        db=db,
        id=project_id,
        customer_id=settings.DEFAULT_CUSTOMER_ID,
    )
    if not project:
        logger.warning("Project detail requested for missing project_id=%s", project_id)
        raise HTTPException(status_code=404, detail="Project not found.")

    return ProjectOut.model_validate(project)

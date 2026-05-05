"""Project CRUD operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session, noload, selectinload

from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.models import (
    CreativePack,
    DesignSpec,
    ExportArtifact,
    GenerationJob,
    Project,
    ProviderRun,
    UploadedAsset,
)
from listingautopilot.logging import get_logger

from ..schemas.projects import (
    ProjectCreate,
    ProjectSearchRequest,
    ProjectStatusEnum,
    ProjectUpdate,
    StrSearchInField,
)


logger = get_logger(__name__)


# --- CREATE ---
def create_project(
    user_context: UserContext, db: Session, obj_in: ProjectCreate
) -> Project:
    try:
        db_obj = Project(
            name=obj_in.name,
            brand_name=obj_in.brand_name,
            product_name=obj_in.product_name,
            category=obj_in.category,
            status=ProjectStatusEnum.RUNNING.value,
            request_payload=obj_in.request_payload,
            customer_id=user_context.customer_id,
            created_by=user_context.id,
        )

        db.add(db_obj)
        db.flush()

        if obj_in.request_payload:
            image_filename = obj_in.request_payload.get("image_filename")
            image_content_type = obj_in.request_payload.get("image_content_type")
            if image_filename and image_content_type:
                db.add(
                    UploadedAsset(
                        project_id=db_obj.id,
                        file_name=image_filename,
                        content_type=image_content_type,
                        storage_url=None,
                        asset_metadata={
                            "request_id": obj_in.request_payload.get("request_id"),
                            "source": "upload",
                        },
                        customer_id=user_context.customer_id,
                    )
                )

        db.add(
            GenerationJob(
                project_id=db_obj.id,
                status=ProjectStatusEnum.RUNNING.value,
                progress_percent=10,
                job_metadata={"stage": "generation_started"},
                customer_id=user_context.customer_id,
            )
        )
        db.commit()
        db.refresh(db_obj)
        logger.info(
            "Project created project_id=%s customer_id=%s name=%s",
            db_obj.id,
            user_context.customer_id,
            db_obj.name,
        )
        return db_obj

    except IntegrityError:
        db.rollback()
        logger.exception("Database error during project creation")
        raise HTTPException(
            status_code=400, detail="Database error during project creation."
        )


# --- GET ONE ---
def get_project(db: Session, id: UUID, customer_id: str) -> Optional[Project]:
    return (
        db.query(Project)
        .filter(
            Project.id == id,
            Project.customer_id == customer_id,
            Project.is_deleted.is_(False),
        )
        .first()
    )


def load_project_details(db: Session, project_id: UUID) -> Project:
    return (
        db.query(Project)
        .options(
            selectinload(Project.assets),
            selectinload(Project.image_assets),
            selectinload(Project.provider_runs),
            selectinload(Project.creative_packs),
            selectinload(Project.design_specs),
            selectinload(Project.editable_designs),
            selectinload(Project.exports),
            noload(Project.jobs),
        )
        .filter(Project.id == project_id)
        .one()
    )


# --- LIST MANY ---
def list_projects(
    db: Session,
    customer_id: str,
    skip: int,
    limit: int,
    sort: List[str],
    sort_dir: List[str],
) -> List[Project]:
    query = db.query(Project).filter(
        Project.customer_id == customer_id, Project.is_deleted.is_(False)
    )
    query = apply_sorting(query, Project, sort, sort_dir)
    return query.offset(skip).limit(limit).all()


def list_recent_projects(
    db: Session,
    customer_id: str,
    limit: int = 5,
) -> List[Project]:
    return (
        db.query(Project)
        .filter(Project.customer_id == customer_id, Project.is_deleted.is_(False))
        .order_by(desc(Project.updated_at))
        .limit(limit)
        .all()
    )


# --- UPDATE ---
def update_project(
    db: Session, db_obj: Project, obj_in: ProjectUpdate
) -> Project:
    if obj_in.name is not None:
        db_obj.name = obj_in.name
    if obj_in.brand_name is not None:
        db_obj.brand_name = obj_in.brand_name
    if obj_in.product_name is not None:
        db_obj.product_name = obj_in.product_name
    if obj_in.category is not None:
        db_obj.category = obj_in.category
    if obj_in.status is not None:
        db_obj.status = obj_in.status.value
    if obj_in.request_payload is not None:
        db_obj.request_payload = obj_in.request_payload
    if obj_in.response_payload is not None:
        db_obj.response_payload = obj_in.response_payload
    if obj_in.score_payload is not None:
        db_obj.score_payload = obj_in.score_payload

    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_project_by_id(
    db: Session, project_id: UUID, customer_id: str, obj_in: ProjectUpdate
) -> Project:
    db_obj = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.customer_id == customer_id,
            Project.is_deleted.is_(False),
        )
        .first()
    )

    if not db_obj:
        logger.warning(
            "Project update requested for missing project_id=%s customer_id=%s",
            project_id,
            customer_id,
        )
        raise HTTPException(status_code=404, detail="Project not found.")

    return update_project(db, db_obj, obj_in)


def update_project_status(
    db: Session,
    project_id: UUID,
    customer_id: str,
    status: ProjectStatusEnum,
    response_payload: dict | None = None,
    score_payload: dict | None = None,
    error_message: str | None = None,
) -> Project:
    db_obj = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.customer_id == customer_id,
            Project.is_deleted.is_(False),
        )
        .first()
    )

    if not db_obj:
        logger.warning(
            "Project status update requested for missing project_id=%s customer_id=%s",
            project_id,
            customer_id,
        )
        raise HTTPException(status_code=404, detail="Project not found.")

    db_obj.status = status.value
    if response_payload is not None:
        db_obj.response_payload = response_payload
    if score_payload is not None:
        db_obj.score_payload = score_payload

    job = (
        db.query(GenerationJob)
        .filter(
            GenerationJob.project_id == project_id,
            GenerationJob.customer_id == customer_id,
            GenerationJob.is_deleted.is_(False),
        )
        .order_by(desc(GenerationJob.created_at))
        .first()
    )
    if job:
        job.status = status.value
        job.progress_percent = 100 if status == ProjectStatusEnum.COMPLETED else job.progress_percent
        if status == ProjectStatusEnum.FAILED:
            job.error_message = error_message or "Generation failed."
            job.job_metadata = {"stage": "generation_failed"}
        elif status == ProjectStatusEnum.COMPLETED:
            job.job_metadata = {"stage": "generation_completed"}

    if response_payload:
        creative_pack = response_payload.get("creative_pack")
        editable_design = response_payload.get("editable_design")
        exports = response_payload.get("exports")
        llm_provider = response_payload.get("llm_provider", "demo")
        llm_model = response_payload.get("llm_model")
        mode = response_payload.get("mode", "demo")

        if creative_pack:
            db.add(
                CreativePack(
                    project_id=db_obj.id,
                    data=creative_pack,
                    customer_id=customer_id,
                )
            )
        if editable_design:
            db.add(
                DesignSpec(
                    project_id=db_obj.id,
                    data=editable_design,
                    customer_id=customer_id,
                )
            )
        if exports:
            db.add(
                ExportArtifact(
                    project_id=db_obj.id,
                    export_type="markdown",
                    data={"content": exports.get("markdown", "")},
                    customer_id=customer_id,
                )
            )
            db.add(
                ExportArtifact(
                    project_id=db_obj.id,
                    export_type="design_json",
                    data={"content": exports.get("design_json", "")},
                    customer_id=customer_id,
                )
            )
        db.add(
            ProviderRun(
                project_id=db_obj.id,
                provider_type=llm_provider,
                model=llm_model,
                mode=mode,
                success=True,
                provider_metadata={"request_id": response_payload.get("request_id", "")},
                customer_id=customer_id,
            )
        )

    db.commit()
    db.refresh(db_obj)
    logger.info(
        "Project status updated project_id=%s customer_id=%s status=%s",
        project_id,
        customer_id,
        status.value,
    )
    return db_obj


# --- DELETE ---
def delete_project(
    db: Session, id: UUID, customer_id: str, *, hard_delete: bool = False
) -> None:
    obj = (
        db.query(Project)
        .filter(Project.id == id, Project.customer_id == customer_id)
        .first()
    )

    if obj:
        if hard_delete:
            db.delete(obj)
        else:
            obj.is_deleted = True
            obj.deleted_at = datetime.now(timezone.utc)
        db.commit()


# --- RESTORE DELETED ---
def undelete_project(
    db: Session, id: UUID, customer_id: str
) -> Optional[Project]:
    obj = (
        db.query(Project)
        .filter(
            Project.id == id,
            Project.customer_id == customer_id,
            Project.is_deleted.is_(True),
        )
        .first()
    )
    if obj:
        obj.is_deleted = False
        obj.deleted_at = None
        db.commit()
        db.refresh(obj)
        return obj
    return None


# --- LIST DELETED ---
def list_deleted_projects(
    db: Session,
    customer_id: str,
    skip: int = 0,
    limit: int = 10,
    sort: List[str] = ["created_at"],
    sort_dir: List[str] = ["desc"],
) -> List[Project]:
    query = db.query(Project).filter(
        Project.customer_id == customer_id, Project.is_deleted.is_(True)
    )
    query = apply_sorting(query, Project, sort, sort_dir)
    return query.offset(skip).limit(limit).all()


# --- ADVANCED SEARCH ---
def apply_str_search(query: Query, model, search: StrSearchInField) -> Query:
    column = getattr(model, search.field, None)
    if not column:
        return query
    condition = (
        column.like(f"%{search.value}%")
        if search.case_sensitive
        else column.ilike(f"%{search.value}%")
    )
    return query.filter(condition)


def apply_sorting(
    query: Query, model, sort_fields: List[str], directions: List[str]
) -> Query:
    for field, dir_ in zip(sort_fields, directions):
        column = getattr(model, field, None)
        if column is not None:
            query = query.order_by(asc(column) if dir_ == "asc" else desc(column))
    return query


def search_projects(
    db: Session, customer_id: str, req: ProjectSearchRequest
) -> List[Project]:
    query = db.query(Project).filter(Project.customer_id == customer_id)

    if not req.include_deleted:
        query = query.filter(Project.is_deleted.is_(False))

    if req.criteria.name:
        query = apply_str_search(query, Project, req.criteria.name)
    if req.criteria.product_name:
        query = apply_str_search(query, Project, req.criteria.product_name)
    if req.criteria.brand_name:
        query = apply_str_search(query, Project, req.criteria.brand_name)

    query = apply_sorting(query, Project, req.sort, req.sort_dir)
    return query.offset(req.skip).limit(req.limit).all()

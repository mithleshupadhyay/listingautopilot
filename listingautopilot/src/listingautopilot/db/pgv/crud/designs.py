"""Editable design CRUD operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session, selectinload

from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.models import EditableDesign, ImageAsset, Project
from listingautopilot.logging import get_logger

from ..schemas.designs import (
    EditableDesignCreate,
    EditableDesignSearchRequest,
    EditableDesignStatusEnum,
    EditableDesignUpdate,
    StrSearchInField,
)


logger = get_logger(__name__)


# --- CREATE ---
def create_editable_design(
    user_context: UserContext, db: Session, obj_in: EditableDesignCreate
) -> EditableDesign:
    try:
        project = (
            db.query(Project)
            .filter(
                Project.id == obj_in.project_id,
                Project.customer_id == user_context.customer_id,
                Project.is_deleted.is_(False),
            )
            .first()
        )

        if not project:
            logger.warning(
                "Editable design creation requested for missing project_id=%s customer_id=%s",
                obj_in.project_id,
                user_context.customer_id,
            )
            raise HTTPException(status_code=404, detail="Project not found.")

        if obj_in.preview_asset_id is not None:
            asset = (
                db.query(ImageAsset)
                .filter(
                    ImageAsset.id == obj_in.preview_asset_id,
                    ImageAsset.customer_id == user_context.customer_id,
                    ImageAsset.is_deleted.is_(False),
                )
                .first()
            )
            if not asset:
                logger.warning(
                    "Editable design creation requested with missing preview_asset_id=%s",
                    obj_in.preview_asset_id,
                )
                raise HTTPException(status_code=404, detail="Preview asset not found.")

        db_obj = EditableDesign(
            project_id=obj_in.project_id,
            name=obj_in.name,
            design_type=obj_in.design_type.value,
            version=obj_in.version,
            canvas_width=obj_in.canvas_width,
            canvas_height=obj_in.canvas_height,
            design_payload=obj_in.design_payload,
            preview_asset_id=obj_in.preview_asset_id,
            status=obj_in.status.value,
            customer_id=user_context.customer_id,
            created_by=user_context.id,
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(
            "Editable design created design_id=%s project_id=%s status=%s",
            db_obj.id,
            db_obj.project_id,
            db_obj.status,
        )
        return db_obj

    except IntegrityError:
        db.rollback()
        logger.exception(
            "Database error during editable design creation project_id=%s",
            obj_in.project_id,
        )
        raise HTTPException(
            status_code=400, detail="Database error during editable design creation."
        )


# --- GET ONE ---
def get_editable_design(
    db: Session, id: UUID, customer_id: str
) -> Optional[EditableDesign]:
    return (
        db.query(EditableDesign)
        .options(selectinload(EditableDesign.preview_asset))
        .filter(
            EditableDesign.id == id,
            EditableDesign.customer_id == customer_id,
            EditableDesign.is_deleted.is_(False),
        )
        .first()
    )


# --- LIST MANY ---
def list_project_designs(
    db: Session,
    project_id: UUID,
    customer_id: str,
    skip: int = 0,
    limit: int = 20,
    sort: List[str] = ["created_at"],
    sort_dir: List[str] = ["desc"],
) -> List[EditableDesign]:
    query = db.query(EditableDesign).filter(
        EditableDesign.project_id == project_id,
        EditableDesign.customer_id == customer_id,
        EditableDesign.is_deleted.is_(False),
    )
    query = apply_sorting(query, EditableDesign, sort, sort_dir)
    return query.offset(skip).limit(limit).all()


def list_recent_editable_designs(
    db: Session,
    customer_id: str,
    limit: int = 10,
) -> List[EditableDesign]:
    return (
        db.query(EditableDesign)
        .filter(
            EditableDesign.customer_id == customer_id,
            EditableDesign.is_deleted.is_(False),
        )
        .order_by(desc(EditableDesign.updated_at))
        .limit(limit)
        .all()
    )


# --- UPDATE ---
def update_editable_design(
    db: Session, db_obj: EditableDesign, obj_in: EditableDesignUpdate
) -> EditableDesign:
    if obj_in.name is not None:
        db_obj.name = obj_in.name
    if obj_in.design_type is not None:
        db_obj.design_type = obj_in.design_type.value
    if obj_in.version is not None:
        db_obj.version = obj_in.version
    if obj_in.canvas_width is not None:
        db_obj.canvas_width = obj_in.canvas_width
    if obj_in.canvas_height is not None:
        db_obj.canvas_height = obj_in.canvas_height
    if obj_in.design_payload is not None:
        db_obj.design_payload = obj_in.design_payload
    if obj_in.preview_asset_id is not None:
        db_obj.preview_asset_id = obj_in.preview_asset_id
    if obj_in.status is not None:
        db_obj.status = obj_in.status.value
    if obj_in.error_message is not None:
        db_obj.error_message = obj_in.error_message

    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_editable_design_by_id(
    db: Session, design_id: UUID, customer_id: str, obj_in: EditableDesignUpdate
) -> EditableDesign:
    db_obj = (
        db.query(EditableDesign)
        .filter(
            EditableDesign.id == design_id,
            EditableDesign.customer_id == customer_id,
            EditableDesign.is_deleted.is_(False),
        )
        .first()
    )

    if not db_obj:
        logger.warning(
            "Editable design update requested for missing design_id=%s customer_id=%s",
            design_id,
            customer_id,
        )
        raise HTTPException(status_code=404, detail="Editable design not found.")

    return update_editable_design(db, db_obj, obj_in)


def attach_design_preview(
    db: Session, design_id: UUID, customer_id: str, preview_asset_id: UUID
) -> EditableDesign:
    db_obj = (
        db.query(EditableDesign)
        .filter(
            EditableDesign.id == design_id,
            EditableDesign.customer_id == customer_id,
            EditableDesign.is_deleted.is_(False),
        )
        .first()
    )

    if not db_obj:
        logger.warning(
            "Attach preview requested for missing design_id=%s customer_id=%s",
            design_id,
            customer_id,
        )
        raise HTTPException(status_code=404, detail="Editable design not found.")

    asset = (
        db.query(ImageAsset)
        .filter(
            ImageAsset.id == preview_asset_id,
            ImageAsset.customer_id == customer_id,
            ImageAsset.is_deleted.is_(False),
        )
        .first()
    )
    if not asset:
        logger.warning(
            "Attach preview requested with missing preview_asset_id=%s customer_id=%s",
            preview_asset_id,
            customer_id,
        )
        raise HTTPException(status_code=404, detail="Preview asset not found.")

    db_obj.preview_asset_id = preview_asset_id
    db_obj.status = EditableDesignStatusEnum.RENDERED.value
    db.commit()
    db.refresh(db_obj)
    logger.info(
        "Editable design preview attached design_id=%s preview_asset_id=%s",
        design_id,
        preview_asset_id,
    )
    return db_obj


# --- DELETE ---
def delete_editable_design(
    db: Session, id: UUID, customer_id: str, *, hard_delete: bool = False
) -> None:
    obj = (
        db.query(EditableDesign)
        .filter(EditableDesign.id == id, EditableDesign.customer_id == customer_id)
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
def undelete_editable_design(
    db: Session, id: UUID, customer_id: str
) -> Optional[EditableDesign]:
    obj = (
        db.query(EditableDesign)
        .filter(
            EditableDesign.id == id,
            EditableDesign.customer_id == customer_id,
            EditableDesign.is_deleted.is_(True),
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
def list_deleted_editable_designs(
    db: Session,
    customer_id: str,
    skip: int = 0,
    limit: int = 10,
    sort: List[str] = ["created_at"],
    sort_dir: List[str] = ["desc"],
) -> List[EditableDesign]:
    query = db.query(EditableDesign).filter(
        EditableDesign.customer_id == customer_id,
        EditableDesign.is_deleted.is_(True),
    )
    query = apply_sorting(query, EditableDesign, sort, sort_dir)
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


def search_editable_designs(
    db: Session, customer_id: str, req: EditableDesignSearchRequest
) -> List[EditableDesign]:
    query = db.query(EditableDesign).filter(EditableDesign.customer_id == customer_id)

    if not req.include_deleted:
        query = query.filter(EditableDesign.is_deleted.is_(False))

    if req.criteria.name:
        query = apply_str_search(query, EditableDesign, req.criteria.name)
    if req.criteria.design_type:
        query = apply_str_search(query, EditableDesign, req.criteria.design_type)
    if req.criteria.status:
        query = apply_str_search(query, EditableDesign, req.criteria.status)

    query = apply_sorting(query, EditableDesign, req.sort, req.sort_dir)
    return query.offset(req.skip).limit(req.limit).all()

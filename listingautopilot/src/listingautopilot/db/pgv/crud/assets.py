"""Image asset CRUD operations."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.models import ImageAsset, Project
from listingautopilot.logging import get_logger

from ..schemas.assets import (
    ImageAssetCreate,
    ImageAssetSearchRequest,
    ImageAssetUpdate,
    StrSearchInField,
)


logger = get_logger(__name__)


# --- CREATE ---
def create_image_asset(
    user_context: UserContext, db: Session, obj_in: ImageAssetCreate
) -> ImageAsset:
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
                "Image asset creation requested for missing project_id=%s customer_id=%s",
                obj_in.project_id,
                user_context.customer_id,
            )
            raise HTTPException(status_code=404, detail="Project not found.")

        db_obj = ImageAsset(
            project_id=obj_in.project_id,
            asset_type=obj_in.asset_type.value,
            file_name=obj_in.file_name,
            content_type=obj_in.content_type,
            storage_path=obj_in.storage_path,
            public_url=obj_in.public_url,
            width=obj_in.width,
            height=obj_in.height,
            file_size_bytes=obj_in.file_size_bytes,
            provider=obj_in.provider,
            asset_metadata=obj_in.asset_metadata,
            customer_id=user_context.customer_id,
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        logger.info(
            "Image asset created asset_id=%s project_id=%s type=%s",
            db_obj.id,
            db_obj.project_id,
            db_obj.asset_type,
        )
        return db_obj

    except IntegrityError:
        db.rollback()
        logger.exception(
            "Database error during image asset creation project_id=%s type=%s",
            obj_in.project_id,
            obj_in.asset_type.value,
        )
        raise HTTPException(
            status_code=400, detail="Database error during image asset creation."
        )


# --- GET ONE ---
def get_image_asset(db: Session, id: UUID, customer_id: str) -> Optional[ImageAsset]:
    return (
        db.query(ImageAsset)
        .filter(
            ImageAsset.id == id,
            ImageAsset.customer_id == customer_id,
            ImageAsset.is_deleted.is_(False),
        )
        .first()
    )


# --- LIST MANY ---
def list_project_image_assets(
    db: Session,
    project_id: UUID,
    customer_id: str,
    skip: int = 0,
    limit: int = 20,
    sort: List[str] = ["created_at"],
    sort_dir: List[str] = ["desc"],
) -> List[ImageAsset]:
    query = db.query(ImageAsset).filter(
        ImageAsset.project_id == project_id,
        ImageAsset.customer_id == customer_id,
        ImageAsset.is_deleted.is_(False),
    )
    query = apply_sorting(query, ImageAsset, sort, sort_dir)
    return query.offset(skip).limit(limit).all()


def list_recent_image_assets(
    db: Session,
    customer_id: str,
    limit: int = 10,
) -> List[ImageAsset]:
    return (
        db.query(ImageAsset)
        .filter(
            ImageAsset.customer_id == customer_id,
            ImageAsset.is_deleted.is_(False),
        )
        .order_by(desc(ImageAsset.created_at))
        .limit(limit)
        .all()
    )


# --- UPDATE ---
def update_image_asset(
    db: Session, db_obj: ImageAsset, obj_in: ImageAssetUpdate
) -> ImageAsset:
    if obj_in.asset_type is not None:
        db_obj.asset_type = obj_in.asset_type.value
    if obj_in.file_name is not None:
        db_obj.file_name = obj_in.file_name
    if obj_in.content_type is not None:
        db_obj.content_type = obj_in.content_type
    if obj_in.storage_path is not None:
        db_obj.storage_path = obj_in.storage_path
    if obj_in.public_url is not None:
        db_obj.public_url = obj_in.public_url
    if obj_in.width is not None:
        db_obj.width = obj_in.width
    if obj_in.height is not None:
        db_obj.height = obj_in.height
    if obj_in.file_size_bytes is not None:
        db_obj.file_size_bytes = obj_in.file_size_bytes
    if obj_in.provider is not None:
        db_obj.provider = obj_in.provider
    if obj_in.asset_metadata is not None:
        db_obj.asset_metadata = obj_in.asset_metadata

    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_image_asset_by_id(
    db: Session, asset_id: UUID, customer_id: str, obj_in: ImageAssetUpdate
) -> ImageAsset:
    db_obj = (
        db.query(ImageAsset)
        .filter(
            ImageAsset.id == asset_id,
            ImageAsset.customer_id == customer_id,
            ImageAsset.is_deleted.is_(False),
        )
        .first()
    )

    if not db_obj:
        logger.warning(
            "Image asset update requested for missing asset_id=%s customer_id=%s",
            asset_id,
            customer_id,
        )
        raise HTTPException(status_code=404, detail="Image asset not found.")

    return update_image_asset(db, db_obj, obj_in)


# --- DELETE ---
def delete_image_asset(
    db: Session, id: UUID, customer_id: str, *, hard_delete: bool = False
) -> None:
    obj = (
        db.query(ImageAsset)
        .filter(ImageAsset.id == id, ImageAsset.customer_id == customer_id)
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
def undelete_image_asset(
    db: Session, id: UUID, customer_id: str
) -> Optional[ImageAsset]:
    obj = (
        db.query(ImageAsset)
        .filter(
            ImageAsset.id == id,
            ImageAsset.customer_id == customer_id,
            ImageAsset.is_deleted.is_(True),
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
def list_deleted_image_assets(
    db: Session,
    customer_id: str,
    skip: int = 0,
    limit: int = 10,
    sort: List[str] = ["created_at"],
    sort_dir: List[str] = ["desc"],
) -> List[ImageAsset]:
    query = db.query(ImageAsset).filter(
        ImageAsset.customer_id == customer_id, ImageAsset.is_deleted.is_(True)
    )
    query = apply_sorting(query, ImageAsset, sort, sort_dir)
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


def search_image_assets(
    db: Session, customer_id: str, req: ImageAssetSearchRequest
) -> List[ImageAsset]:
    query = db.query(ImageAsset).filter(ImageAsset.customer_id == customer_id)

    if not req.include_deleted:
        query = query.filter(ImageAsset.is_deleted.is_(False))

    if req.criteria.file_name:
        query = apply_str_search(query, ImageAsset, req.criteria.file_name)
    if req.criteria.provider:
        query = apply_str_search(query, ImageAsset, req.criteria.provider)
    if req.criteria.asset_type:
        query = apply_str_search(query, ImageAsset, req.criteria.asset_type)

    query = apply_sorting(query, ImageAsset, req.sort, req.sort_dir)
    return query.offset(req.skip).limit(req.limit).all()

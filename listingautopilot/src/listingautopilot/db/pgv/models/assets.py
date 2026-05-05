"""Image asset persistence models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from listingautopilot.db.pgv.db import Base


JsonColumn = JSONB().with_variant(JSON(), "sqlite")


class ImageAsset(Base):
    __tablename__ = "image_assets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(String(64), nullable=False, index=True)
    file_name = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=False)
    storage_path = Column(Text, nullable=True)
    public_url = Column(Text, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    provider = Column(String(64), nullable=False, default="demo", index=True)
    asset_metadata = Column(JsonColumn, nullable=True)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="image_assets", lazy="noload")
    preview_designs = relationship(
        "EditableDesign",
        back_populates="preview_asset",
        lazy="noload",
        foreign_keys="EditableDesign.preview_asset_id",
    )

    __table_args__ = (
        Index("ix_image_assets_project_type", "project_id", "asset_type"),
        Index("ix_image_assets_customer_type", "customer_id", "asset_type"),
    )


"""Editable design persistence models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from listingautopilot.db.pgv.db import Base


JsonColumn = JSONB().with_variant(JSON(), "sqlite")


class EditableDesign(Base):
    __tablename__ = "editable_designs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(256), nullable=False, index=True)
    design_type = Column(String(64), nullable=False, index=True)
    version = Column(String(32), nullable=False, default="1.0")
    canvas_width = Column(Integer, nullable=False, default=2000)
    canvas_height = Column(Integer, nullable=False, default=2000)
    design_payload = Column(JsonColumn, nullable=False)
    preview_asset_id = Column(Uuid(as_uuid=True), ForeignKey("image_assets.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(64), nullable=False, default="draft", index=True)
    error_message = Column(Text, nullable=True)
    customer_id = Column(String(64), nullable=False, index=True)
    created_by = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="editable_designs", lazy="noload")
    preview_asset = relationship(
        "ImageAsset",
        back_populates="preview_designs",
        lazy="selectin",
        foreign_keys=[preview_asset_id],
    )

    __table_args__ = (
        Index("ix_editable_designs_project_type", "project_id", "design_type"),
        Index("ix_editable_designs_customer_status", "customer_id", "status"),
    )


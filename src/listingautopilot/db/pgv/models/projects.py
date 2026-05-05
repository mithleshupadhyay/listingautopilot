"""Project persistence models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from listingautopilot.db.pgv.db import Base


JsonColumn = JSONB().with_variant(JSON(), "sqlite")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(256), nullable=False, index=True)
    brand_name = Column(String(256), nullable=True, index=True)
    product_name = Column(String(256), nullable=True, index=True)
    category = Column(String(256), nullable=True, index=True)
    status = Column(String(64), nullable=False, default="draft", index=True)
    request_payload = Column(JsonColumn, nullable=True)
    response_payload = Column(JsonColumn, nullable=True)
    score_payload = Column(JsonColumn, nullable=True)
    customer_id = Column(String(64), nullable=False, index=True)
    created_by = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    assets = relationship("UploadedAsset", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    image_assets = relationship("ImageAsset", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    jobs = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    creative_packs = relationship("CreativePack", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    design_specs = relationship("DesignSpec", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    editable_designs = relationship("EditableDesign", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    exports = relationship("ExportArtifact", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    provider_runs = relationship("ProviderRun", back_populates="project", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("ix_projects_customer_deleted", "customer_id", "is_deleted"),
        Index("ix_projects_customer_status", "customer_id", "status"),
        Index("ix_projects_customer_updated", "customer_id", "updated_at"),
    )


class UploadedAsset(Base):
    __tablename__ = "uploaded_assets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(512), nullable=False)
    content_type = Column(String(128), nullable=False)
    storage_url = Column(Text, nullable=True)
    asset_metadata = Column(JsonColumn, nullable=True)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="assets", lazy="noload")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(64), nullable=False, default="queued", index=True)
    progress_percent = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    job_metadata = Column(JsonColumn, nullable=True)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="jobs", lazy="noload")


class ProviderRun(Base):
    __tablename__ = "provider_runs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_type = Column(String(64), nullable=False, index=True)
    model = Column(String(256), nullable=True)
    mode = Column(String(64), nullable=False, default="demo", index=True)
    latency_ms = Column(String(32), nullable=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    provider_metadata = Column(JsonColumn, nullable=True)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="provider_runs", lazy="noload")


class CreativePack(Base):
    __tablename__ = "creative_packs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    data = Column(JsonColumn, nullable=False)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="creative_packs", lazy="noload")


class DesignSpec(Base):
    __tablename__ = "design_specs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    data = Column(JsonColumn, nullable=False)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="design_specs", lazy="noload")


class ExportArtifact(Base):
    __tablename__ = "export_artifacts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    export_type = Column(String(64), nullable=False, index=True)
    data = Column(JsonColumn, nullable=False)
    customer_id = Column(String(64), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="exports", lazy="noload")

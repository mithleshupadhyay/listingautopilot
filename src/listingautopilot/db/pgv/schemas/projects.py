"""Project persistence schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatusEnum(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1)
    brand_name: str | None = None
    product_name: str | None = None
    category: str | None = None
    request_payload: dict[str, Any] | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    brand_name: str | None = None
    product_name: str | None = None
    category: str | None = None
    status: ProjectStatusEnum | None = None
    request_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None
    score_payload: dict[str, Any] | None = None


class ProjectOut(BaseModel):
    id: UUID
    name: str
    brand_name: str | None = None
    product_name: str | None = None
    category: str | None = None
    status: str
    request_payload: dict[str, Any] | None = None
    response_payload: dict[str, Any] | None = None
    score_payload: dict[str, Any] | None = None
    customer_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class ProjectSummaryOut(BaseModel):
    id: UUID
    name: str
    brand_name: str | None = None
    product_name: str | None = None
    category: str | None = None
    status: str
    score_payload: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StrSearchInField(BaseModel):
    field: str
    value: str
    case_sensitive: bool = False


class ProjectSearchCriteria(BaseModel):
    name: StrSearchInField | None = None
    product_name: StrSearchInField | None = None
    brand_name: StrSearchInField | None = None


class ProjectSearchRequest(BaseModel):
    criteria: ProjectSearchCriteria = Field(default_factory=ProjectSearchCriteria)
    include_deleted: bool = False
    skip: int = 0
    limit: int = 20
    sort: list[str] = ["created_at"]
    sort_dir: list[str] = ["desc"]

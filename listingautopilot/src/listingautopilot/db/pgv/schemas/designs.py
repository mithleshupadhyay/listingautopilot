"""Editable design persistence schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DesignTypeEnum(str, Enum):
    MAIN_IMAGE = "main_image"
    INFOGRAPHIC = "infographic"
    LIFESTYLE = "lifestyle"


class EditableDesignStatusEnum(str, Enum):
    DRAFT = "draft"
    RENDERED = "rendered"
    FAILED = "failed"


class EditableDesignCreate(BaseModel):
    project_id: UUID
    name: str = Field(..., min_length=1)
    design_type: DesignTypeEnum = DesignTypeEnum.INFOGRAPHIC
    version: str = "1.0"
    canvas_width: int = Field(default=2000, gt=0)
    canvas_height: int = Field(default=2000, gt=0)
    design_payload: dict[str, Any]
    preview_asset_id: UUID | None = None
    status: EditableDesignStatusEnum = EditableDesignStatusEnum.DRAFT


class EditableDesignUpdate(BaseModel):
    name: str | None = None
    design_type: DesignTypeEnum | None = None
    version: str | None = None
    canvas_width: int | None = Field(default=None, gt=0)
    canvas_height: int | None = Field(default=None, gt=0)
    design_payload: dict[str, Any] | None = None
    preview_asset_id: UUID | None = None
    status: EditableDesignStatusEnum | None = None
    error_message: str | None = None


class EditableDesignOut(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    design_type: str
    version: str
    canvas_width: int
    canvas_height: int
    design_payload: dict[str, Any]
    preview_asset_id: UUID | None = None
    status: str
    error_message: str | None = None
    customer_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class StrSearchInField(BaseModel):
    field: str
    value: str
    case_sensitive: bool = False


class EditableDesignSearchCriteria(BaseModel):
    name: StrSearchInField | None = None
    design_type: StrSearchInField | None = None
    status: StrSearchInField | None = None


class EditableDesignSearchRequest(BaseModel):
    criteria: EditableDesignSearchCriteria = Field(
        default_factory=EditableDesignSearchCriteria
    )
    include_deleted: bool = False
    skip: int = 0
    limit: int = 20
    sort: list[str] = ["created_at"]
    sort_dir: list[str] = ["desc"]


"""Image asset persistence schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ImageAssetTypeEnum(str, Enum):
    ORIGINAL_UPLOAD = "original_upload"
    UPGRADED_PRODUCT = "upgraded_product"
    DESIGN_PREVIEW = "design_preview"
    LIFESTYLE = "lifestyle"
    EXPORT = "export"


class ImageAssetCreate(BaseModel):
    project_id: UUID
    asset_type: ImageAssetTypeEnum
    file_name: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    storage_path: str | None = None
    public_url: str | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    file_size_bytes: int | None = Field(default=None, ge=0)
    provider: str = "demo"
    asset_metadata: dict[str, Any] | None = None


class ImageAssetUpdate(BaseModel):
    asset_type: ImageAssetTypeEnum | None = None
    file_name: str | None = None
    content_type: str | None = None
    storage_path: str | None = None
    public_url: str | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    file_size_bytes: int | None = Field(default=None, ge=0)
    provider: str | None = None
    asset_metadata: dict[str, Any] | None = None


class ImageAssetOut(BaseModel):
    id: UUID
    project_id: UUID
    asset_type: str
    file_name: str
    content_type: str
    storage_path: str | None = None
    public_url: str | None = None
    width: int | None = None
    height: int | None = None
    file_size_bytes: int | None = None
    provider: str
    asset_metadata: dict[str, Any] | None = None
    customer_id: str
    created_at: datetime
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)


class StrSearchInField(BaseModel):
    field: str
    value: str
    case_sensitive: bool = False


class ImageAssetSearchCriteria(BaseModel):
    file_name: StrSearchInField | None = None
    provider: StrSearchInField | None = None
    asset_type: StrSearchInField | None = None


class ImageAssetSearchRequest(BaseModel):
    criteria: ImageAssetSearchCriteria = Field(default_factory=ImageAssetSearchCriteria)
    include_deleted: bool = False
    skip: int = 0
    limit: int = 20
    sort: list[str] = ["created_at"]
    sort_dir: list[str] = ["desc"]


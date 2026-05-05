"""Response schemas for generation."""

from typing import Literal

from pydantic import BaseModel, Field

from listingautopilot.llm.schemas import CreativePackDraft, DesignSpecDraft, ProductAnalysisDraft


class ImageBundle(BaseModel):
    original_url: str | None = None
    upgraded_url: str | None = None
    design_preview_url: str | None = None
    lifestyle_url: str | None = None
    provider: str = "demo"
    metadata: dict[str, str] = Field(default_factory=dict)


class ListingScore(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    image_quality: int = Field(..., ge=0, le=100)
    amazon_readiness: int = Field(..., ge=0, le=100)
    conversion_potential: int = Field(..., ge=0, le=100)
    benefit_clarity: int = Field(..., ge=0, le=100)
    proof_readiness: int = Field(..., ge=0, le=100)
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ExportBundle(BaseModel):
    markdown: str
    design_json: str


class GenerateResponse(BaseModel):
    request_id: str
    mode: Literal["demo", "live", "mixed"] = "demo"
    project_id: str | None = None
    llm_provider: str = "demo"
    llm_model: str = "demo-listing-autopilot"
    image_provider: str = "demo"
    product: ProductAnalysisDraft
    score: ListingScore
    creative_pack: CreativePackDraft
    images: ImageBundle
    editable_design: DesignSpecDraft
    exports: ExportBundle
    warnings: list[str] = Field(default_factory=list)

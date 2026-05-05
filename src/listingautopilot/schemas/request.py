"""Request schemas for generation."""

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    product_name: str | None = None
    brand_name: str | None = None
    category: str | None = None
    target_customer: str | None = None
    brand_tone: str = "clear, premium, Amazon-friendly"
    amazon_listing_url: str | None = None
    competitor_url: str | None = None
    image_filename: str = Field(..., min_length=1)
    image_content_type: str = Field(..., min_length=1)
    image_bytes: bytes
    llm_provider: str = "demo"
    use_demo_mode: bool = False
    save_to_db: bool = False

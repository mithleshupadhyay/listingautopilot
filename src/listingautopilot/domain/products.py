"""Product domain primitives."""

from pydantic import BaseModel


class ProductContext(BaseModel):
    product_name: str | None = None
    brand_name: str | None = None
    category: str | None = None
    target_customer: str | None = None
    brand_tone: str = "clear, premium, Amazon-friendly"
    amazon_listing_url: str | None = None
    competitor_url: str | None = None

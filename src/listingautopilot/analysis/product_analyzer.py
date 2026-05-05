"""Product analyzer facade."""

from listingautopilot.llm.client import analyze_product_image
from listingautopilot.llm.schemas import LLMProviderSettings, ProductAnalysisDraft


def analyze_product(
    llm_client: LLMProviderSettings,
    image_bytes: bytes,
    image_filename: str,
    context: dict[str, str | None],
) -> ProductAnalysisDraft:
    return analyze_product_image(
        llm_client=llm_client,
        image_bytes=image_bytes,
        image_filename=image_filename,
        context=context,
    )

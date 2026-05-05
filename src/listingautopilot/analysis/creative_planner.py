"""Creative pack planner facade."""

from listingautopilot.llm.client import generate_creative_pack
from listingautopilot.llm.schemas import (
    CreativePackDraft,
    LLMProviderSettings,
    ProductAnalysisDraft,
)


def plan_creative_pack(
    llm_client: LLMProviderSettings,
    product_analysis: ProductAnalysisDraft,
    context: dict[str, str | None],
) -> CreativePackDraft:
    return generate_creative_pack(
        llm_client=llm_client,
        product_analysis=product_analysis,
        context=context,
    )

"""Design JSON builder facade."""

from listingautopilot.llm.client import generate_design_spec
from listingautopilot.llm.schemas import CreativePackDraft, DesignSpecDraft, LLMProviderSettings


def build_design_json(
    llm_client: LLMProviderSettings,
    creative_pack: CreativePackDraft,
    upgraded_image_ref: str | None,
) -> DesignSpecDraft:
    return generate_design_spec(
        llm_client=llm_client,
        creative_pack=creative_pack,
        upgraded_image_ref=upgraded_image_ref,
    )

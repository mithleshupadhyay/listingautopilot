"""Design JSON exporter."""

from listingautopilot.llm.schemas import DesignSpecDraft


def export_design_json(design_spec: DesignSpecDraft) -> str:
    return design_spec.model_dump_json(indent=2)

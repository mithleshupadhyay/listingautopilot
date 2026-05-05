"""Markdown report exporter."""

from listingautopilot.llm.schemas import CreativePackDraft, DesignSpecDraft, ProductAnalysisDraft
from listingautopilot.schemas.response import ListingScore


def export_markdown_report(
    product: ProductAnalysisDraft,
    score: ListingScore,
    creative_pack: CreativePackDraft,
    design_spec: DesignSpecDraft,
) -> str:
    lines = [
        f"# Listing Autopilot Report: {product.product_name}",
        "",
        f"Category: {product.category}",
        f"Target customer: {product.target_customer}",
        f"Overall score: {score.overall}/100",
        "",
        "## Product Summary",
        "",
        product.description,
        "",
        "## Issues",
        "",
    ]
    lines.extend(f"- {issue}" for issue in score.issues)
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in score.recommendations)
    lines.extend(["", "## Amazon Title", "", creative_pack.amazon_title, "", "## Bullets", ""])
    lines.extend(f"- {bullet}" for bullet in creative_pack.bullets)
    lines.extend(["", "## Purchase Criteria", ""])
    lines.extend(f"- {criterion}" for criterion in creative_pack.purchase_criteria)
    lines.extend(["", "## Editable Design", "", f"Layers: {len(design_spec.layers)}"])
    return "\n".join(lines)

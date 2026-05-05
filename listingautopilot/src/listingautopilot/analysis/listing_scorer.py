"""Listing readiness scoring."""

from listingautopilot.llm.schemas import CreativePackDraft, ProductAnalysisDraft
from listingautopilot.schemas.response import ListingScore


def score_listing(
    product_analysis: ProductAnalysisDraft,
    creative_pack: CreativePackDraft,
    image_provider: str,
) -> ListingScore:
    issues: list[str] = []
    recommendations: list[str] = []

    image_quality = 72
    amazon_readiness = 70
    conversion_potential = 74
    benefit_clarity = 70
    proof_readiness = 68

    if product_analysis.visual_issues:
        image_quality -= min(18, len(product_analysis.visual_issues) * 4)
        for issue in product_analysis.visual_issues[:4]:
            issues.append(issue)

    if image_provider == "demo":
        issues.append("Live image provider is not configured; demo image upgrade was used.")
        recommendations.append("Connect Cloudinary, Replicate, or another image provider for real image transformation.")
    else:
        image_quality += 8
        amazon_readiness += 8

    if len(creative_pack.infographic_callouts) >= 3:
        benefit_clarity += 10
        proof_readiness += 8
    else:
        issues.append("Infographic needs at least three benefit callouts.")
        recommendations.append("Add three clear product benefits as editable callout layers.")

    if len(creative_pack.purchase_criteria) >= 5:
        conversion_potential += 8
    else:
        recommendations.append("Expand purchase criteria so the creative direction reflects buyer decision factors.")

    recommendations.extend(
        [
            "Use a centered main image on a clean white background.",
            "Turn the top three purchase criteria into infographic callouts.",
            "Add a lifestyle scene that demonstrates the primary use case.",
        ]
    )

    image_quality = max(0, min(100, image_quality))
    amazon_readiness = max(0, min(100, amazon_readiness))
    conversion_potential = max(0, min(100, conversion_potential))
    benefit_clarity = max(0, min(100, benefit_clarity))
    proof_readiness = max(0, min(100, proof_readiness))
    overall = round(
        (
            image_quality
            + amazon_readiness
            + conversion_potential
            + benefit_clarity
            + proof_readiness
        )
        / 5
    )

    return ListingScore(
        overall=overall,
        image_quality=image_quality,
        amazon_readiness=amazon_readiness,
        conversion_potential=conversion_potential,
        benefit_clarity=benefit_clarity,
        proof_readiness=proof_readiness,
        issues=list(dict.fromkeys(issues)),
        recommendations=list(dict.fromkeys(recommendations)),
    )

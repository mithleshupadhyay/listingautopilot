"""Prompt builders for provider-independent structured generation."""

from __future__ import annotations

import json

from listingautopilot.llm.schemas import CreativePackDraft, DesignSpecDraft, ProductAnalysisDraft


SYSTEM_PROMPT = """You are an ecommerce creative strategist for Amazon listings.
Turn product inputs into clear, conversion-focused creative direction.
Avoid unsupported claims. Prefer concrete visible benefits and buyer criteria.
Return only valid JSON matching the requested schema."""


def build_product_analysis_prompt(context: dict[str, str | None]) -> str:
    return _build_prompt(
        task="Analyze the uploaded product image and optional listing context.",
        context=context,
        schema=ProductAnalysisDraft.model_json_schema(),
        requirements=[
            "Infer only what is visible or reasonably likely from context.",
            "Focus on Amazon listing usefulness.",
            "Call out image quality issues that affect selling.",
        ],
    )


def build_creative_pack_prompt(product_analysis: dict, context: dict[str, str | None]) -> str:
    return _build_prompt(
        task="Create an Amazon listing creative pack from the product analysis.",
        context={"product_analysis": json.dumps(product_analysis), **context},
        schema=CreativePackDraft.model_json_schema(),
        requirements=[
            "Write marketplace-friendly copy.",
            "Do not invent regulated claims.",
            "Make purchase criteria specific and useful for visual design.",
            "Bullets should be concise and benefit-led.",
        ],
    )


def build_design_spec_prompt(creative_pack: dict, upgraded_image_ref: str | None) -> str:
    return _build_prompt(
        task="Create editable design JSON for a 2000x2000 Amazon infographic image.",
        context={
            "creative_pack": json.dumps(creative_pack),
            "upgraded_image_ref": upgraded_image_ref,
        },
        schema=DesignSpecDraft.model_json_schema(),
        requirements=[
            "Use a 2000x2000 white canvas.",
            "Include one image layer for the product.",
            "Include one headline layer and at least three callout or badge layers.",
            "Keep all layers inside canvas bounds.",
            "Use readable font sizes and high contrast.",
            "Use most of the canvas. Do not make the product or text tiny.",
            "The product image layer should usually be at least 900px wide or 1100px tall.",
            "The primary headline should be easy to read when previewed at dashboard size.",
            "Use renderer style keys: font_size, font_weight, color, fill, radius, text_align.",
            "Do not use CSS px strings or camelCase style keys in the returned JSON.",
        ],
    )


def _build_prompt(
    *,
    task: str,
    context: dict,
    schema: dict,
    requirements: list[str],
) -> str:
    return json.dumps(
        {
            "task": task,
            "context": context,
            "requirements": requirements,
            "return_json_schema": schema,
        },
        indent=2,
    )

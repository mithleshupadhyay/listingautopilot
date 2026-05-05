"""Provider-specific LLM calls in direct service-function style."""

from __future__ import annotations

import base64
import json
import mimetypes
from typing import Any

from pydantic import ValidationError

from listingautopilot.llm.prompts import (
    SYSTEM_PROMPT,
    build_creative_pack_prompt,
    build_design_spec_prompt,
    build_product_analysis_prompt,
)
from listingautopilot.llm.schemas import (
    AnthropicProviderConfig,
    CreativePackDraft,
    DesignSpecDraft,
    GeminiProviderConfig,
    LLMProviderSettings,
    OpenAIProviderConfig,
    ProductAnalysisDraft,
    ProviderType,
)


class LLMClientError(RuntimeError):
    """Raised when a provider call fails or returns invalid structured data."""


# --- PRODUCT ANALYSIS ---
def analyze_product_image(
    llm_client: LLMProviderSettings,
    image_bytes: bytes,
    image_filename: str,
    context: dict[str, str | None],
) -> ProductAnalysisDraft:
    provider_type = ProviderType(llm_client.provider_type)

    if provider_type == ProviderType.DEMO:
        stem = image_filename.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        cleaned = stem.replace("_", " ").replace("-", " ").strip()
        product_name = context.get("product_name") or (
            cleaned.title() if cleaned else "Uploaded Product"
        )
        category = context.get("category") or "Amazon product"
        target_customer = (
            context.get("target_customer")
            or "online shoppers comparing practical everyday products"
        )
        return ProductAnalysisDraft(
            product_name=product_name,
            category=category,
            description=f"{product_name} prepared for an Amazon listing creative workflow.",
            visible_features=[
                "single hero product photo",
                "supplier-style visual input",
                "needs cleaner ecommerce presentation",
            ],
            likely_use_cases=[
                "Amazon main image",
                "lifestyle listing image",
                "benefit-led infographic",
            ],
            target_customer=target_customer,
            visual_issues=[
                "background may not meet clean marketplace expectations",
                "benefits are not communicated visually",
                "image does not include conversion-focused proof points",
            ],
            selling_angles=[
                "make the main product easier to inspect",
                "translate visible features into buyer benefits",
                "create editable callouts for listing optimization",
            ],
        )

    if provider_type == ProviderType.OPENAI:
        config = llm_client.config
        if not isinstance(config, OpenAIProviderConfig) or not config.is_configured():
            raise LLMClientError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        kwargs: dict[str, Any] = {"api_key": config.api_key_value()}
        if config.endpoint:
            kwargs["base_url"] = config.endpoint
        client = OpenAI(**kwargs)

        mime_type = mimetypes.guess_type(image_filename)[0] or "image/jpeg"
        encoded = base64.b64encode(image_bytes).decode("ascii")
        image_url = f"data:{mime_type};base64,{encoded}"
        prompt = build_product_analysis_prompt(context)
        response = client.responses.create(
            model=config.model,
            instructions=SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                }
            ],
            temperature=config.params.temperature,
            max_output_tokens=config.params.max_tokens,
            text={"format": {"type": "json_object"}},
        )

        try:
            text = response.output_text.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return ProductAnalysisDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("ProductAnalysisDraft provider response was not valid JSON") from exc

    if provider_type == ProviderType.GEMINI:
        config = llm_client.config
        if not isinstance(config, GeminiProviderConfig) or not config.is_configured():
            raise LLMClientError("GEMINI_API_KEY is not configured")

        import google.generativeai as genai

        genai.configure(api_key=config.api_key_value())
        model = genai.GenerativeModel(
            model_name=config.model,
            system_instruction=SYSTEM_PROMPT,
        )
        prompt = build_product_analysis_prompt(context)
        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": mimetypes.guess_type(image_filename)[0] or "image/jpeg",
                    "data": image_bytes,
                },
            ],
            generation_config={
                "temperature": config.params.temperature,
                "max_output_tokens": config.params.max_tokens,
                "response_mime_type": "application/json",
            },
        )

        try:
            text = getattr(response, "text", "").strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return ProductAnalysisDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("ProductAnalysisDraft provider response was not valid JSON") from exc

    if provider_type == ProviderType.ANTHROPIC:
        config = llm_client.config
        if not isinstance(config, AnthropicProviderConfig) or not config.is_configured():
            raise LLMClientError("ANTHROPIC_API_KEY is not configured")

        from anthropic import Anthropic

        client = Anthropic(api_key=config.api_key_value())
        prompt = build_product_analysis_prompt(context)
        response = client.messages.create(
            model=config.model,
            max_tokens=config.params.max_tokens,
            temperature=config.params.temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mimetypes.guess_type(image_filename)[0]
                                or "image/jpeg",
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        try:
            text = "\n".join(
                block.text for block in response.content if getattr(block, "text", None)
            ).strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return ProductAnalysisDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("ProductAnalysisDraft provider response was not valid JSON") from exc

    raise LLMClientError(f"{provider_type.value} provider is not supported")


# --- CREATIVE PACK ---
def generate_creative_pack(
    llm_client: LLMProviderSettings,
    product_analysis: ProductAnalysisDraft,
    context: dict[str, str | None],
) -> CreativePackDraft:
    provider_type = ProviderType(llm_client.provider_type)

    if provider_type == ProviderType.DEMO:
        product = product_analysis.product_name
        return CreativePackDraft(
            amazon_title=f"{product} for Everyday Use - Clean, Durable, Listing-Ready Design",
            bullets=[
                f"Designed for shoppers who need a reliable {product.lower()} without guesswork",
                "Clean product presentation helps buyers inspect the item quickly",
                "Benefit-led callouts make key features easier to compare",
                "Lifestyle direction shows the product in a realistic use case",
                "Editable design layers make future listing changes faster",
            ],
            benefits=[
                "Clearer product presentation",
                "Faster buyer understanding",
                "Reusable listing creative structure",
            ],
            pain_points=[
                "supplier photos look low trust",
                "listing images do not explain benefits",
                "creative updates require manual design work",
            ],
            purchase_criteria=[
                "visual clarity",
                "trustworthy main image",
                "benefit proof",
                "realistic lifestyle use",
                "easy product comparison",
            ],
            main_image_recommendation="Use a centered product image on a clean white background with balanced contrast and visible edges.",
            lifestyle_concept=f"Show {product.lower()} in a realistic setting where the target customer would naturally use it.",
            infographic_headline=f"Why shoppers choose {product}",
            infographic_callouts=[
                "Clean product view",
                "Benefit-led design",
                "Ready for Amazon",
            ],
            a_plus_sections=[
                "Problem and solution banner",
                "Feature-to-benefit comparison",
                "Use-case grid",
            ],
        )

    if provider_type == ProviderType.OPENAI:
        config = llm_client.config
        if not isinstance(config, OpenAIProviderConfig) or not config.is_configured():
            raise LLMClientError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        kwargs: dict[str, Any] = {"api_key": config.api_key_value()}
        if config.endpoint:
            kwargs["base_url"] = config.endpoint
        client = OpenAI(**kwargs)

        response = client.responses.create(
            model=config.model,
            instructions=SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_creative_pack_prompt(
                                product_analysis.model_dump(), context
                            ),
                        }
                    ],
                }
            ],
            temperature=config.params.temperature,
            max_output_tokens=config.params.max_tokens,
            text={"format": {"type": "json_object"}},
        )

        try:
            text = response.output_text.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return CreativePackDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("CreativePackDraft provider response was not valid JSON") from exc

    if provider_type == ProviderType.GEMINI:
        config = llm_client.config
        if not isinstance(config, GeminiProviderConfig) or not config.is_configured():
            raise LLMClientError("GEMINI_API_KEY is not configured")

        import google.generativeai as genai

        genai.configure(api_key=config.api_key_value())
        model = genai.GenerativeModel(
            model_name=config.model,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            [build_creative_pack_prompt(product_analysis.model_dump(), context)],
            generation_config={
                "temperature": config.params.temperature,
                "max_output_tokens": config.params.max_tokens,
                "response_mime_type": "application/json",
            },
        )

        try:
            text = getattr(response, "text", "").strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return CreativePackDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("CreativePackDraft provider response was not valid JSON") from exc

    if provider_type == ProviderType.ANTHROPIC:
        config = llm_client.config
        if not isinstance(config, AnthropicProviderConfig) or not config.is_configured():
            raise LLMClientError("ANTHROPIC_API_KEY is not configured")

        from anthropic import Anthropic

        client = Anthropic(api_key=config.api_key_value())
        response = client.messages.create(
            model=config.model,
            max_tokens=config.params.max_tokens,
            temperature=config.params.temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": build_creative_pack_prompt(
                                product_analysis.model_dump(), context
                            ),
                        }
                    ],
                }
            ],
        )

        try:
            text = "\n".join(
                block.text for block in response.content if getattr(block, "text", None)
            ).strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return CreativePackDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("CreativePackDraft provider response was not valid JSON") from exc

    raise LLMClientError(f"{provider_type.value} provider is not supported")


# --- DESIGN JSON ---
def generate_design_spec(
    llm_client: LLMProviderSettings,
    creative_pack: CreativePackDraft,
    upgraded_image_ref: str | None,
) -> DesignSpecDraft:
    provider_type = ProviderType(llm_client.provider_type)

    if provider_type == ProviderType.DEMO:
        callouts = creative_pack.infographic_callouts[:3]
        layers = [
            {
                "id": "background",
                "type": "shape",
                "name": "White background",
                "x": 0,
                "y": 0,
                "width": 2000,
                "height": 2000,
                "style": {"fill": "#ffffff"},
            },
            {
                "id": "product-main",
                "type": "image",
                "name": "Product image",
                "x": 610,
                "y": 430,
                "width": 780,
                "height": 980,
                "image_ref": upgraded_image_ref or "uploaded-product",
                "style": {"fit": "contain"},
            },
            {
                "id": "headline",
                "type": "text",
                "name": "Headline",
                "x": 180,
                "y": 120,
                "width": 1640,
                "height": 170,
                "text": creative_pack.infographic_headline,
                "style": {"font_size": 72, "font_weight": "700", "color": "#111827"},
            },
        ]
        positions = [(160, 520), (1450, 760), (180, 1240)]
        for index, callout in enumerate(callouts):
            x, y = positions[index]
            layers.append(
                {
                    "id": f"callout-{index + 1}",
                    "type": "badge",
                    "name": f"Callout {index + 1}",
                    "x": x,
                    "y": y,
                    "width": 420,
                    "height": 150,
                    "text": callout,
                    "style": {
                        "font_size": 42,
                        "font_weight": "650",
                        "color": "#0f172a",
                        "fill": "#e7f3ef",
                        "radius": 28,
                    },
                }
            )
        return DesignSpecDraft(
            layers=layers,
            metadata={
                "source": "listing-autopilot",
                "mode": "demo",
                "format": "editable-design-json",
            },
        )

    if provider_type == ProviderType.OPENAI:
        config = llm_client.config
        if not isinstance(config, OpenAIProviderConfig) or not config.is_configured():
            raise LLMClientError("OPENAI_API_KEY is not configured")

        from openai import OpenAI

        kwargs: dict[str, Any] = {"api_key": config.api_key_value()}
        if config.endpoint:
            kwargs["base_url"] = config.endpoint
        client = OpenAI(**kwargs)

        response = client.responses.create(
            model=config.model,
            instructions=SYSTEM_PROMPT,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": build_design_spec_prompt(
                                creative_pack.model_dump(), upgraded_image_ref
                            ),
                        }
                    ],
                }
            ],
            temperature=config.params.temperature,
            max_output_tokens=config.params.max_tokens,
            text={"format": {"type": "json_object"}},
        )

        try:
            text = response.output_text.strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return DesignSpecDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("DesignSpecDraft provider response was not valid JSON") from exc

    if provider_type == ProviderType.GEMINI:
        config = llm_client.config
        if not isinstance(config, GeminiProviderConfig) or not config.is_configured():
            raise LLMClientError("GEMINI_API_KEY is not configured")

        import google.generativeai as genai

        genai.configure(api_key=config.api_key_value())
        model = genai.GenerativeModel(
            model_name=config.model,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            [build_design_spec_prompt(creative_pack.model_dump(), upgraded_image_ref)],
            generation_config={
                "temperature": config.params.temperature,
                "max_output_tokens": config.params.max_tokens,
                "response_mime_type": "application/json",
            },
        )

        try:
            text = getattr(response, "text", "").strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return DesignSpecDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("DesignSpecDraft provider response was not valid JSON") from exc

    if provider_type == ProviderType.ANTHROPIC:
        config = llm_client.config
        if not isinstance(config, AnthropicProviderConfig) or not config.is_configured():
            raise LLMClientError("ANTHROPIC_API_KEY is not configured")

        from anthropic import Anthropic

        client = Anthropic(api_key=config.api_key_value())
        response = client.messages.create(
            model=config.model,
            max_tokens=config.params.max_tokens,
            temperature=config.params.temperature,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": build_design_spec_prompt(
                                creative_pack.model_dump(), upgraded_image_ref
                            ),
                        }
                    ],
                }
            ],
        )

        try:
            text = "\n".join(
                block.text for block in response.content if getattr(block, "text", None)
            ).strip()
            if text.startswith("```"):
                lines = text.splitlines()
                if lines and lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end >= start:
                text = text[start : end + 1]
            return DesignSpecDraft.model_validate(json.loads(text))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LLMClientError("DesignSpecDraft provider response was not valid JSON") from exc

    raise LLMClientError(f"{provider_type.value} provider is not supported")

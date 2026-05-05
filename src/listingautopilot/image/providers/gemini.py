"""Gemini image editing provider."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from uuid import uuid4

import requests

from listingautopilot.config import settings
from listingautopilot.exceptions import ProviderExecutionError
from listingautopilot.image.providers.common import (
    build_amazon_image_edit_prompt,
    save_provider_image_as_png,
)
from listingautopilot.logging import get_logger
from listingautopilot.schemas.response import ImageBundle


logger = get_logger(__name__)


def upgrade_image_gemini(
    image_bytes: bytes,
    image_filename: str,
    image_content_type: str = "image/png",
    context: dict[str, str | None] | None = None,
) -> ImageBundle:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ProviderExecutionError(
            "GEMINI_API_KEY is required for Gemini image editing.",
            code="GEMINI_IMAGE_PROVIDER_NOT_CONFIGURED",
        )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(image_filename).suffix or ".jpg"
    original_path = settings.output_dir / f"original-{uuid4().hex[:10]}{suffix}"
    upgraded_path = settings.output_dir / f"upgraded-amazon-gemini-{uuid4().hex[:10]}.png"
    original_path.write_bytes(image_bytes)

    base_url = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
    endpoint = f"{base_url}/models/{settings.gemini_image_model}:generateContent"
    prompt = build_amazon_image_edit_prompt(
        image_filename=image_filename,
        context=context,
    )
    response = requests.post(
        endpoint,
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": image_content_type or "image/png",
                                "data": base64.b64encode(image_bytes).decode("utf-8"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": settings.gemini_image_aspect_ratio,
                    "imageSize": settings.gemini_image_size,
                },
            },
        },
        timeout=settings.image_provider_timeout_seconds,
    )
    if response.status_code >= 400:
        logger.error(
            "Gemini image edit failed status=%s body=%s",
            response.status_code,
            response.text[:1000],
        )
        raise ProviderExecutionError(
            f"Gemini image edit failed with status {response.status_code}.",
            code="GEMINI_IMAGE_EDIT_FAILED",
        )

    payload = response.json()
    edited_bytes = None
    text_parts: list[str] = []
    finish_reasons: list[str] = []
    for candidate in payload.get("candidates", []):
        finish_reason = candidate.get("finishReason")
        if finish_reason:
            finish_reasons.append(str(finish_reason))
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            if part.get("text"):
                text_parts.append(str(part["text"]))
            inline_data = part.get("inlineData") or part.get("inline_data")
            if not inline_data:
                continue
            data = inline_data.get("data")
            if data:
                edited_bytes = base64.b64decode(data)
                break
        if edited_bytes:
            break

    if not edited_bytes:
        detail = " ".join(text_parts).strip()
        if not detail and finish_reasons:
            detail = f"finishReason={', '.join(finish_reasons)}"
        prompt_feedback = payload.get("promptFeedback") or payload.get("prompt_feedback")
        if not detail and prompt_feedback:
            detail = f"promptFeedback={prompt_feedback}"
        logger.error(
            "Gemini image edit returned no image model=%s detail=%s payload_keys=%s",
            settings.gemini_image_model,
            detail[:1000] if detail else "no text detail",
            sorted(payload.keys()),
        )
        raise ProviderExecutionError(
            "Gemini image edit response did not include image data."
            + (f" Gemini returned: {detail[:500]}" if detail else ""),
            code="GEMINI_IMAGE_RESPONSE_EMPTY",
        )

    try:
        save_provider_image_as_png(edited_bytes, upgraded_path)
    except Exception as exc:
        raise ProviderExecutionError(
            "Gemini image edit returned data that could not be saved as an image.",
            code="GEMINI_IMAGE_SAVE_FAILED",
        ) from exc

    logger.info(
        "Gemini image upgrade completed filename=%s original_url=%s upgraded_url=%s model=%s",
        image_filename,
        original_path,
        upgraded_path,
        settings.gemini_image_model,
    )
    return ImageBundle(
        original_url=str(original_path),
        upgraded_url=str(upgraded_path),
        provider="gemini",
        metadata={
            "note": "Gemini image model produced a real AI-edited Amazon-ready product image.",
            "original_filename": image_filename,
            "image_model": settings.gemini_image_model,
            "image_aspect_ratio": settings.gemini_image_aspect_ratio,
            "image_size": settings.gemini_image_size,
            "upgraded_format": "png",
            "canvas": "2000x2000",
        },
    )

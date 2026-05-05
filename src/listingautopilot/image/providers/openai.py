"""OpenAI image editing provider."""

from __future__ import annotations

import base64
import os
from io import BytesIO
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


def upgrade_image_openai(
    image_bytes: bytes,
    image_filename: str,
    image_content_type: str = "image/png",
    context: dict[str, str | None] | None = None,
) -> ImageBundle:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ProviderExecutionError(
            "OPENAI_API_KEY is required for OpenAI image editing.",
            code="OPENAI_IMAGE_PROVIDER_NOT_CONFIGURED",
        )

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(image_filename).suffix or ".jpg"
    original_path = settings.output_dir / f"original-{uuid4().hex[:10]}{suffix}"
    upgraded_path = settings.output_dir / f"upgraded-amazon-openai-{uuid4().hex[:10]}.png"
    original_path.write_bytes(image_bytes)

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    endpoint = f"{base_url}/images/edits"
    prompt = build_amazon_image_edit_prompt(
        image_filename=image_filename,
        context=context,
    )
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}"},
        data={
            "model": settings.openai_image_model,
            "prompt": prompt,
            "size": settings.openai_image_size,
            "quality": settings.openai_image_quality,
            "output_format": settings.openai_image_output_format,
            "background": "opaque",
            "n": "1",
        },
        files={
            "image": (
                image_filename,
                BytesIO(image_bytes),
                image_content_type or "application/octet-stream",
            )
        },
        timeout=settings.image_provider_timeout_seconds,
    )
    if response.status_code >= 400:
        logger.error(
            "OpenAI image edit failed status=%s body=%s",
            response.status_code,
            response.text[:1000],
        )
        raise ProviderExecutionError(
            f"OpenAI image edit failed with status {response.status_code}.",
            code="OPENAI_IMAGE_EDIT_FAILED",
        )

    payload = response.json()
    image_data = (payload.get("data") or [{}])[0]
    b64_json = image_data.get("b64_json")
    image_url = image_data.get("url")
    if b64_json:
        edited_bytes = base64.b64decode(b64_json)
    elif image_url:
        image_response = requests.get(
            image_url,
            timeout=settings.image_provider_timeout_seconds,
        )
        if image_response.status_code >= 400:
            raise ProviderExecutionError(
                f"OpenAI image URL download failed with status {image_response.status_code}.",
                code="OPENAI_IMAGE_DOWNLOAD_FAILED",
            )
        edited_bytes = image_response.content
    else:
        raise ProviderExecutionError(
            "OpenAI image edit response did not include image data.",
            code="OPENAI_IMAGE_RESPONSE_EMPTY",
        )

    try:
        save_provider_image_as_png(edited_bytes, upgraded_path)
    except Exception as exc:
        raise ProviderExecutionError(
            "OpenAI image edit returned data that could not be saved as an image.",
            code="OPENAI_IMAGE_SAVE_FAILED",
        ) from exc

    logger.info(
        "OpenAI image upgrade completed filename=%s original_url=%s upgraded_url=%s model=%s",
        image_filename,
        original_path,
        upgraded_path,
        settings.openai_image_model,
    )
    return ImageBundle(
        original_url=str(original_path),
        upgraded_url=str(upgraded_path),
        provider="openai",
        metadata={
            "note": "OpenAI image edit produced a real AI-edited Amazon-ready product image.",
            "original_filename": image_filename,
            "image_model": settings.openai_image_model,
            "image_size": settings.openai_image_size,
            "image_quality": settings.openai_image_quality,
            "upgraded_format": "png",
            "canvas": "2000x2000",
        },
    )

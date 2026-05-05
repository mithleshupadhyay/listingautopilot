"""Editable design preview renderer."""

from __future__ import annotations

import textwrap
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont, ImageOps

from listingautopilot.config import settings
from listingautopilot.image.providers.common import crop_to_visual_content
from listingautopilot.logging import get_logger
from listingautopilot.llm.schemas import DesignSpecDraft


logger = get_logger(__name__)


def render_design_preview(design_spec: DesignSpecDraft) -> str:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = settings.output_dir / f"editable-design-preview-{uuid4().hex[:10]}.png"
    canvas = Image.new(
        "RGBA",
        (design_spec.canvas.width, design_spec.canvas.height),
        design_spec.canvas.background,
    )
    draw = ImageDraw.Draw(canvas)

    for layer in design_spec.layers:
        if layer.type == "shape":
            fill = layer.style.get("fill") or layer.style.get("backgroundColor") or "#ffffff"
            radius = layer.style.get("radius") or layer.style.get("borderRadius") or 0
            if isinstance(radius, str):
                radius = radius.strip().lower().replace("px", "")
            radius = int(radius or 0)
            if radius > 0:
                draw.rounded_rectangle(
                    (layer.x, layer.y, layer.x + layer.width, layer.y + layer.height),
                    radius=radius,
                    fill=fill,
                )
            else:
                draw.rectangle(
                    (layer.x, layer.y, layer.x + layer.width, layer.y + layer.height),
                    fill=fill,
                )

        if layer.type == "image":
            try:
                image_ref = Path(layer.image_ref or "")
                image = Image.open(image_ref)
                image = ImageOps.exif_transpose(image).convert("RGBA")
            except Exception:
                logger.warning(
                    "Design renderer could not load image layer=%s image_ref=%s",
                    layer.id,
                    layer.image_ref,
                )
                image = Image.new("RGBA", (layer.width, layer.height), (241, 245, 249, 255))
                image_draw = ImageDraw.Draw(image)
                image_draw.rounded_rectangle(
                    (30, 30, layer.width - 30, layer.height - 30),
                    radius=32,
                    fill=(255, 255, 255, 255),
                    outline=(148, 163, 184, 255),
                    width=5,
                )
            else:
                image = crop_to_visual_content(image, threshold=14, padding_ratio=0.02)
            scale = min(layer.width / max(image.width, 1), layer.height / max(image.height, 1))
            if scale <= 0:
                scale = 1
            image = image.resize(
                (
                    max(1, int(image.width * scale)),
                    max(1, int(image.height * scale)),
                ),
                Image.Resampling.LANCZOS,
            )
            x = layer.x + (layer.width - image.width) // 2
            y = layer.y + (layer.height - image.height) // 2
            canvas.alpha_composite(image, (x, y))

        if layer.type in {"text", "badge"}:
            fill = layer.style.get("fill") or layer.style.get("backgroundColor")
            radius = layer.style.get("radius") or layer.style.get("borderRadius") or 24
            if isinstance(radius, str):
                radius = radius.strip().lower().replace("px", "")
            radius = int(radius or 24)
            if layer.type == "badge":
                draw.rounded_rectangle(
                    (layer.x, layer.y, layer.x + layer.width, layer.y + layer.height),
                    radius=radius,
                    fill=fill or "#e7f3ef",
                    outline=layer.style.get("outline", "#b7d8cf"),
                    width=2,
                )

            color = layer.style.get("color", "#111827")
            font_size = layer.style.get("font_size") or layer.style.get("fontSize") or 42
            if isinstance(font_size, str):
                font_size = font_size.strip().lower().replace("px", "")
            font_size = int(font_size or 42)
            font_weight = str(
                layer.style.get("font_weight") or layer.style.get("fontWeight") or "400"
            )
            font_name = "DejaVuSans-Bold.ttf" if font_weight != "400" else "DejaVuSans.ttf"
            try:
                font = ImageFont.truetype(font_name, font_size)
            except OSError:
                font = ImageFont.load_default()

            text = layer.text or ""
            padding = layer.style.get("padding", 0) or 0
            if isinstance(padding, str):
                padding = padding.strip().lower().replace("px", "")
            padding = int(padding or 0)
            text_align = str(
                layer.style.get("text_align") or layer.style.get("textAlign") or "center"
            )
            text_width_limit = max(8, layer.width - (padding * 2))
            max_chars = max(8, int(text_width_limit / max(font_size * 0.54, 1)))
            lines = textwrap.wrap(text, width=max_chars) or [text]
            line_height = int(font_size * 1.18)
            total_height = line_height * len(lines)
            text_y = layer.y + max(0, (layer.height - total_height) // 2)
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                if text_align == "left":
                    text_x = layer.x + padding
                elif text_align == "right":
                    text_x = layer.x + max(0, text_width_limit - text_width) + padding
                else:
                    text_x = layer.x + max(0, (layer.width - text_width) // 2)
                draw.text((text_x, text_y), line, fill=color, font=font)
                text_y += line_height

    canvas.convert("RGB").save(preview_path, format="PNG", optimize=True)
    logger.info(
        "Editable design preview rendered preview_url=%s layers=%s",
        preview_path,
        len(design_spec.layers),
    )
    return str(preview_path)


def get_image_size(path: str | None) -> tuple[int | None, int | None, int | None]:
    if not path:
        return None, None, None

    image_path = Path(path)
    if not image_path.exists():
        logger.warning("Image metadata requested for missing path=%s", path)
        return None, None, None

    try:
        with Image.open(image_path) as image:
            width, height = image.size
    except Exception:
        logger.exception("Failed to read image metadata path=%s", path)
        width = None
        height = None

    return width, height, image_path.stat().st_size

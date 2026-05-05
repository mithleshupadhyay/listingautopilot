"""Shared image provider helpers."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


def build_amazon_image_edit_prompt(
    image_filename: str,
    context: dict[str, str | None] | None = None,
) -> str:
    product_name = (context or {}).get("product_name") or Path(image_filename).stem
    category = (context or {}).get("category") or "ecommerce product"
    target_customer = (context or {}).get("target_customer") or "Amazon shopper"
    brand_tone = (context or {}).get("brand_tone") or "clear, premium, Amazon-friendly"

    return (
        "Edit the uploaded product photo into an Amazon-ready studio product image. "
        f"Product: {product_name}. Category: {category}. Target buyer: {target_customer}. "
        f"Visual tone: {brand_tone}. "
        "Preserve the exact product identity, packaging, logo, labels, shape, color, and visible product text. "
        "Do not invent new claims, badges, labels, text, hands, props, people, or extra products. "
        "Remove messy background, scanner borders, black frame lines, clutter, harsh shadows, and low-quality lighting. "
        "Place the sellable product centered on a pure white ecommerce background with natural studio lighting, "
        "clean edges, balanced contrast, and a subtle realistic floor shadow. "
        "The product must be large in frame, occupying roughly 80 to 90 percent of the image height or width. "
        "Do not leave a tiny product floating in excessive whitespace. "
        "For apparel or fashion, preserve the garment and any existing model wearing it, and frame the outfit large enough "
        "for shoppers to inspect fabric, pattern, and fit. "
        "Do not create an infographic, collage, split-screen, or multiple product copies. "
        "Return only the edited product image."
    )


def edge_background_color(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    samples = []
    step_x = max(1, width // 28)
    step_y = max(1, height // 28)

    for x in range(0, width, step_x):
        samples.append(rgb.getpixel((x, 0)))
        samples.append(rgb.getpixel((x, height - 1)))
    for y in range(0, height, step_y):
        samples.append(rgb.getpixel((0, y)))
        samples.append(rgb.getpixel((width - 1, y)))

    middle = len(samples) // 2
    return (
        sorted(pixel[0] for pixel in samples)[middle],
        sorted(pixel[1] for pixel in samples)[middle],
        sorted(pixel[2] for pixel in samples)[middle],
    )


def crop_to_visual_content(
    image: Image.Image,
    threshold: int = 18,
    padding_ratio: float = 0.035,
) -> Image.Image:
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox:
        image = image.crop(alpha_bbox)

    background = edge_background_color(image)
    diff = ImageChops.difference(image.convert("RGB"), Image.new("RGB", image.size, background))
    mask = diff.convert("L").point(lambda value: 255 if value > threshold else 0)
    mask = mask.filter(ImageFilter.MaxFilter(5))
    bbox = mask.getbbox()
    if not bbox:
        return image

    width, height = image.size
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]
    coverage = (bbox_width * bbox_height) / max(width * height, 1)
    if coverage < 0.01 or coverage > 0.96:
        return image

    padding = int(max(width, height) * padding_ratio)
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(width, bbox[2] + padding)
    bottom = min(height, bbox[3] + padding)
    return image.crop((left, top, right, bottom))


def normalize_product_image(
    image: Image.Image,
    canvas_size: int = 2000,
    max_width: int = 1780,
    max_height: int = 1860,
) -> Image.Image:
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    image = crop_to_visual_content(image, threshold=16, padding_ratio=0.025)
    image = crop_to_visual_content(image, threshold=10, padding_ratio=0.03)
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
    scale = min(max_width / max(image.width, 1), max_height / max(image.height, 1))
    if scale <= 0:
        scale = 1
    image = image.resize(
        (
            max(1, int(image.width * scale)),
            max(1, int(image.height * scale)),
        ),
        Image.Resampling.LANCZOS,
    )
    x = (canvas_size - image.width) // 2
    y = max(40, (canvas_size - image.height) // 2 - 15)

    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_width = max(220, int(image.width * 0.68))
    shadow_height = max(28, int(image.height * 0.055))
    shadow_x = x + (image.width - shadow_width) // 2
    shadow_y = min(canvas_size - 95, y + image.height - int(shadow_height * 0.25))
    shadow_draw.ellipse(
        (shadow_x, shadow_y, shadow_x + shadow_width, shadow_y + shadow_height),
        fill=(15, 23, 42, 34),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.alpha_composite(image, (x, y))
    return canvas


def save_provider_image_as_png(image_bytes: bytes, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.open(BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image).convert("RGBA")
    canvas = normalize_product_image(image)
    canvas.convert("RGB").save(output_path, format="PNG", optimize=True)

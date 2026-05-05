"""Demo image provider."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

from listingautopilot.config import settings
from listingautopilot.logging import get_logger
from listingautopilot.schemas.response import ImageBundle


logger = get_logger(__name__)


def _edge_background_color(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    samples = []
    step_x = max(1, width // 24)
    step_y = max(1, height // 24)
    for x in range(0, width, step_x):
        samples.append(rgb.getpixel((x, 0)))
        samples.append(rgb.getpixel((x, height - 1)))
    for y in range(0, height, step_y):
        samples.append(rgb.getpixel((0, y)))
        samples.append(rgb.getpixel((width - 1, y)))

    red = sorted(pixel[0] for pixel in samples)
    green = sorted(pixel[1] for pixel in samples)
    blue = sorted(pixel[2] for pixel in samples)
    middle = len(samples) // 2
    return red[middle], green[middle], blue[middle]


def _crop_to_visual_content(image: Image.Image, threshold: int = 22, padding_ratio: float = 0.045) -> Image.Image:
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    alpha_bbox = image.getchannel("A").getbbox()
    if alpha_bbox:
        image = image.crop(alpha_bbox)

    background = _edge_background_color(image)
    diff = ImageChops.difference(image.convert("RGB"), Image.new("RGB", image.size, background))
    mask = diff.convert("L").point(lambda value: 255 if value > threshold else 0)
    bbox = mask.getbbox()
    if not bbox:
        return image

    width, height = image.size
    bbox_width = bbox[2] - bbox[0]
    bbox_height = bbox[3] - bbox[1]
    if bbox_width * bbox_height < width * height * 0.015:
        return image

    padding = int(max(width, height) * padding_ratio)
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(width, bbox[2] + padding)
    bottom = min(height, bbox[3] + padding)
    return image.crop((left, top, right, bottom))


def _remove_scanner_frame_lines(image: Image.Image) -> Image.Image:
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    width, height = image.size
    if width < 80 or height < 80:
        return image

    gray = image.convert("L")
    clean = image.copy()
    draw = ImageDraw.Draw(clean)
    columns_to_clear: list[int] = []
    rows_to_clear: list[int] = []
    outer_left = int(width * 0.2)
    outer_right = int(width * 0.8)
    outer_top = int(height * 0.2)
    outer_bottom = int(height * 0.8)

    for x in range(width):
        if outer_left <= x <= outer_right:
            continue
        histogram = gray.crop((x, 0, x + 1, height)).histogram()
        dark_pixels = sum(histogram[:44])
        if dark_pixels / max(height, 1) > 0.34:
            columns_to_clear.append(x)

    for y in range(height):
        if outer_top <= y <= outer_bottom:
            continue
        histogram = gray.crop((0, y, width, y + 1)).histogram()
        dark_pixels = sum(histogram[:44])
        if dark_pixels / max(width, 1) > 0.34:
            rows_to_clear.append(y)

    for x in columns_to_clear:
        draw.rectangle((max(0, x - 4), 0, min(width, x + 5), height), fill=(255, 255, 255, 0))
    for y in rows_to_clear:
        draw.rectangle((0, max(0, y - 4), width, min(height, y + 5)), fill=(255, 255, 255, 0))

    return clean


def _build_soft_cutout(image: Image.Image) -> tuple[Image.Image, bool]:
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    background = _edge_background_color(image)
    diff = ImageChops.difference(image.convert("RGB"), Image.new("RGB", image.size, background))
    mask = diff.convert("L").point(lambda value: 255 if value > 20 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(1.8))
    bbox = mask.getbbox()
    if not bbox:
        return image, False

    width, height = image.size
    coverage = ((bbox[2] - bbox[0]) * (bbox[3] - bbox[1])) / max(width * height, 1)
    if coverage < 0.04 or coverage > 0.9:
        return image, False

    cutout = image.copy()
    alpha = ImageChops.multiply(image.getchannel("A"), mask)
    cutout.putalpha(alpha)
    return cutout, True


def upgrade_image_demo(image_bytes: bytes, image_filename: str) -> ImageBundle:
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(image_filename).suffix or ".jpg"
    original_path = settings.output_dir / f"original-{uuid4().hex[:10]}{suffix}"
    upgraded_path = settings.output_dir / f"upgraded-amazon-demo-{uuid4().hex[:10]}.png"
    original_path.write_bytes(image_bytes)

    try:
        source = Image.open(BytesIO(image_bytes))
        source = ImageOps.exif_transpose(source).convert("RGBA")
    except Exception:
        logger.warning(
            "Demo image provider could not decode image; using placeholder filename=%s",
            image_filename,
        )
        source = Image.new("RGBA", (900, 900), (241, 245, 249, 255))
        draw = ImageDraw.Draw(source)
        draw.rounded_rectangle(
            (180, 150, 720, 750),
            radius=60,
            fill=(255, 255, 255, 255),
            outline=(148, 163, 184, 255),
            width=8,
        )
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 58)
            small_font = ImageFont.truetype("DejaVuSans.ttf", 34)
        except OSError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        draw.text((270, 370), "PRODUCT", fill=(15, 23, 42, 255), font=font)
        draw.text((278, 450), "preview", fill=(71, 85, 105, 255), font=small_font)

    source = _crop_to_visual_content(source, threshold=18, padding_ratio=0.035)
    source = _remove_scanner_frame_lines(source)
    source = _crop_to_visual_content(source, threshold=18, padding_ratio=0.04)

    alpha = source.getchannel("A")
    enhanced_rgb = ImageOps.autocontrast(source.convert("RGB"), cutoff=1)
    source = enhanced_rgb.convert("RGBA")
    source.putalpha(alpha)
    source = ImageEnhance.Color(source).enhance(1.08)
    source = ImageEnhance.Contrast(source).enhance(1.18)
    source = ImageEnhance.Sharpness(source).enhance(1.35)
    source = ImageEnhance.Brightness(source).enhance(1.04)
    source, cutout_used = _build_soft_cutout(source)
    source = _crop_to_visual_content(source, threshold=12, padding_ratio=0.05)

    canvas_size = 2000
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
    max_width = 1500
    max_height = 1620
    source.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    x = (canvas_size - source.width) // 2
    y = (canvas_size - source.height) // 2 - 35

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    ellipse_width = max(280, int(source.width * 0.78))
    ellipse_height = max(34, int(source.height * 0.075))
    ellipse_x = x + (source.width - ellipse_width) // 2
    ellipse_y = y + source.height - int(ellipse_height * 0.42)
    shadow_draw.ellipse(
        (
            ellipse_x,
            ellipse_y,
            ellipse_x + ellipse_width,
            ellipse_y + ellipse_height,
        ),
        fill=(15, 23, 42, 42 if cutout_used else 22),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(24))
    canvas = Image.alpha_composite(canvas, shadow_layer)
    canvas.alpha_composite(source, (x, y))
    canvas.convert("RGB").save(upgraded_path, format="PNG", optimize=True)
    logger.info(
        "Demo image upgrade completed filename=%s original_url=%s upgraded_url=%s cutout_used=%s",
        image_filename,
        original_path,
        upgraded_path,
        cutout_used,
    )

    return ImageBundle(
        original_url=str(original_path),
        upgraded_url=str(upgraded_path),
        provider="demo",
        metadata={
            "note": "Local provider cropped margins, removed simple scanner frames, cleaned contrast, and rendered a 2000x2000 Amazon-ready white studio canvas.",
            "original_filename": image_filename,
            "upgraded_format": "png",
            "canvas": "2000x2000",
            "background_cleanup": "edge-color crop plus simple frame-line removal",
            "cutout_used": str(cutout_used).lower(),
        },
    )

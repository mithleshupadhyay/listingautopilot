import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from listingautopilot.config import settings
from listingautopilot.image.upgrade_pipeline import upgrade_image


def _png_bytes() -> bytes:
    image = Image.new("RGB", (64, 64), (0, 128, 96))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _small_subject_png_bytes() -> bytes:
    image = Image.new("RGB", (1024, 1024), (255, 255, 255))
    for x in range(470, 554):
        for y in range(410, 650):
            image.putpixel((x, y), (128, 0, 64))
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_openai_image_provider_calls_real_edit_endpoint(monkeypatch, tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

    captured = {}

    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {"data": [{"b64_json": base64.b64encode(_small_subject_png_bytes()).decode("utf-8")}]}

    def fake_post(url, headers, data, files, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["data"] = data
        captured["files"] = files
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("listingautopilot.image.providers.openai.requests.post", fake_post)

    try:
        result = upgrade_image(
            image_bytes=_png_bytes(),
            image_filename="product.png",
            image_content_type="image/png",
            provider_type="openai",
            context={"product_name": "Steel Bottle"},
        )
    finally:
        object.__setattr__(settings, "output_dir", original_output_dir)

    assert result.provider == "openai"
    assert captured["url"].endswith("/images/edits")
    assert captured["data"]["model"] == settings.openai_image_model
    assert Path(result.upgraded_url).exists()
    with Image.open(result.upgraded_url) as image:
        assert image.size == (2000, 2000)
        assert image.getbbox() == (0, 0, 2000, 2000)
        non_white_pixels = sum(
            1
            for pixel in image.convert("RGB").getdata()
            if pixel != (255, 255, 255)
        )
        assert non_white_pixels > 280000


def test_gemini_image_provider_calls_generate_content(monkeypatch, tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    captured = {}

    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": base64.b64encode(_small_subject_png_bytes()).decode("utf-8"),
                                    }
                                }
                            ]
                        }
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("listingautopilot.image.providers.gemini.requests.post", fake_post)

    try:
        result = upgrade_image(
            image_bytes=_png_bytes(),
            image_filename="product.png",
            image_content_type="image/png",
            provider_type="gemini",
            context={"product_name": "Steel Bottle"},
        )
    finally:
        object.__setattr__(settings, "output_dir", original_output_dir)

    assert result.provider == "gemini"
    assert captured["url"].endswith(f"/models/{settings.gemini_image_model}:generateContent")
    assert captured["json"]["generationConfig"]["responseModalities"] == ["IMAGE"]
    assert Path(result.upgraded_url).exists()
    with Image.open(result.upgraded_url) as image:
        assert image.size == (2000, 2000)
        non_white_pixels = sum(
            1
            for pixel in image.convert("RGB").getdata()
            if pixel != (255, 255, 255)
        )
        assert non_white_pixels > 280000


def test_gemini_image_provider_falls_back_to_demo_when_no_image(monkeypatch, tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {"text": "I cannot create an edited image for this request."}
                            ]
                        },
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        return FakeResponse()

    monkeypatch.setattr("listingautopilot.image.providers.gemini.requests.post", fake_post)

    try:
        result = upgrade_image(
            image_bytes=_png_bytes(),
            image_filename="product.png",
            image_content_type="image/png",
            provider_type="gemini",
            context={"product_name": "Steel Bottle"},
        )
    finally:
        object.__setattr__(settings, "output_dir", original_output_dir)

    assert result.provider == "demo"
    assert result.metadata["fallback_from"] == "gemini"
    assert result.metadata["fallback_code"] == "GEMINI_IMAGE_RESPONSE_EMPTY"
    assert "I cannot create an edited image" in result.metadata["fallback_reason"]

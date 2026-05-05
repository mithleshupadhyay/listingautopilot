from listingautopilot.api.generation import generate_listing_pack
from listingautopilot.config import settings
from listingautopilot.schemas.request import GenerateRequest
from PIL import Image


def test_core_pipeline_runs_without_db(tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path)
    try:
        response = generate_listing_pack(
            GenerateRequest(
                product_name="Steel Bottle",
                brand_name="Acme",
                category="Kitchen",
                target_customer="office workers",
                image_filename="steel-bottle.jpg",
                image_content_type="image/jpeg",
                image_bytes=b"fake-image",
                llm_provider="demo",
                use_demo_mode=True,
                save_to_db=False,
            )
        )
    finally:
        object.__setattr__(settings, "output_dir", original_output_dir)

    assert response.project_id is None
    assert response.mode == "demo"
    assert response.product.product_name == "Steel Bottle"
    assert response.score.overall > 0
    assert response.images.upgraded_url
    assert response.images.design_preview_url
    assert response.exports.markdown
    assert response.exports.design_json

    with Image.open(response.images.upgraded_url) as upgraded:
        assert upgraded.size == (2000, 2000)
    with Image.open(response.images.design_preview_url) as preview:
        assert preview.size == (2000, 2000)

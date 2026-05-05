from pathlib import Path

from PIL import Image


def test_generate_endpoint_returns_creative_pack_without_persistence(
    client_without_db,
    sample_product_image_bytes,
):
    response = client_without_db.post(
        "/v1/generate",
        data={
            "product_name": "Eco Bottle",
            "brand_name": "Acme",
            "category": "Kitchen",
            "target_customer": "office workers",
            "brand_tone": "clear, premium, Amazon-friendly",
            "llm_provider": "demo",
            "use_demo_mode": "true",
            "save_to_db": "false",
        },
        files={
            "image": (
                "eco-bottle.png",
                sample_product_image_bytes,
                "image/png",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["project_id"] is None
    assert payload["mode"] == "demo"
    assert payload["llm_provider"] == "demo"
    assert payload["image_provider"] == "demo"
    assert payload["product"]["product_name"] == "Eco Bottle"
    assert payload["score"]["overall"] > 0
    assert payload["creative_pack"]["amazon_title"]
    assert len(payload["creative_pack"]["purchase_criteria"]) >= 5
    assert payload["editable_design"]["canvas"]["width"] == 2000
    assert payload["editable_design"]["canvas"]["height"] == 2000
    assert payload["exports"]["markdown"]
    assert payload["exports"]["design_json"]

    upgraded_path = Path(payload["images"]["upgraded_url"])
    preview_path = Path(payload["images"]["design_preview_url"])
    assert upgraded_path.exists()
    assert preview_path.exists()
    with Image.open(upgraded_path) as upgraded:
        assert upgraded.size == (2000, 2000)
    with Image.open(preview_path) as preview:
        assert preview.size == (2000, 2000)

    recent_response = client_without_db.get("/v1/projects/recent")
    assert recent_response.status_code == 200
    assert recent_response.json() == []


def test_generate_endpoint_rejects_empty_upload(client_without_db):
    response = client_without_db.post(
        "/v1/generate",
        data={
            "product_name": "Empty Product",
            "llm_provider": "demo",
            "save_to_db": "false",
        },
        files={"image": ("empty.jpg", b"", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded image is empty."


def test_generate_endpoint_persists_and_exposes_project_assets_and_designs(
    client_with_db,
    sample_product_image_bytes,
):
    response = client_with_db.post(
        "/v1/generate",
        data={
            "product_name": "Eco Bottle",
            "brand_name": "Acme",
            "category": "Kitchen",
            "target_customer": "office workers",
            "brand_tone": "clear, premium, Amazon-friendly",
            "llm_provider": "demo",
            "use_demo_mode": "true",
            "save_to_db": "true",
        },
        files={
            "image": (
                "eco-bottle.png",
                sample_product_image_bytes,
                "image/png",
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    project_id = payload["project_id"]
    assert project_id

    recent_response = client_with_db.get("/v1/projects/recent?limit=3")
    project_response = client_with_db.get(f"/v1/projects/{project_id}")
    assets_response = client_with_db.get(f"/v1/projects/{project_id}/assets")
    designs_response = client_with_db.get(f"/v1/projects/{project_id}/designs")

    assert recent_response.status_code == 200
    assert recent_response.json()[0]["id"] == project_id
    assert recent_response.json()[0]["status"] == "completed"
    assert recent_response.json()[0]["score_payload"]["overall"] > 0

    assert project_response.status_code == 200
    saved_project = project_response.json()
    assert saved_project["id"] == project_id
    assert saved_project["status"] == "completed"
    assert saved_project["response_payload"]["request_id"] == payload["request_id"]
    assert saved_project["response_payload"]["images"]["upgraded_url"]
    assert saved_project["score_payload"]["overall"] == payload["score"]["overall"]

    assert assets_response.status_code == 200
    assets = assets_response.json()
    assert len(assets) == 3
    assert {asset["asset_type"] for asset in assets} == {
        "original_upload",
        "upgraded_product",
        "design_preview",
    }
    for asset in assets:
        assert asset["project_id"] == project_id
        assert Path(asset["storage_path"]).exists()

    upgraded_asset = next(
        asset for asset in assets if asset["asset_type"] == "upgraded_product"
    )
    asset_response = client_with_db.get(f"/v1/assets/{upgraded_asset['id']}")
    assert asset_response.status_code == 200
    assert asset_response.json()["width"] == 2000
    assert asset_response.json()["height"] == 2000

    assert designs_response.status_code == 200
    designs = designs_response.json()
    assert len(designs) == 1
    assert designs[0]["project_id"] == project_id
    assert designs[0]["status"] == "rendered"
    assert designs[0]["canvas_width"] == 2000
    assert designs[0]["canvas_height"] == 2000
    assert designs[0]["preview_asset_id"]

    design_response = client_with_db.get(f"/v1/designs/{designs[0]['id']}")
    assert design_response.status_code == 200
    assert design_response.json()["design_payload"]["metadata"]["preview_url"]

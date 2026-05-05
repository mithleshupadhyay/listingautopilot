from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from listingautopilot.api.dependencies import get_optional_db
from listingautopilot.api.generation import generate_listing_pack
from listingautopilot.config import settings
from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.crud.projects import load_project_details
from listingautopilot.db.pgv.db import Base
from listingautopilot.db.pgv.models import Project
from listingautopilot.main import app
from listingautopilot.schemas.request import GenerateRequest


def test_assets_and_designs_api_returns_saved_outputs(tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path)
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        response = generate_listing_pack(
            request=GenerateRequest(
                product_name="Desk Lamp",
                brand_name="BrightCo",
                category="Home",
                target_customer="remote workers",
                image_filename="desk-lamp.jpg",
                image_content_type="image/jpeg",
                image_bytes=b"fake-image",
                llm_provider="demo",
                use_demo_mode=True,
                save_to_db=True,
            ),
            db=db,
            user_context=UserContext(
                id=settings.default_user_id,
                customer_id=settings.default_customer_id,
            ),
        )
        saved_project = db.query(Project).first()
        loaded_project = load_project_details(db=db, project_id=saved_project.id)
        asset_id = loaded_project.image_assets[0].id
        design_id = loaded_project.editable_designs[0].id

        def override_db():
            yield db

        app.dependency_overrides[get_optional_db] = override_db
        client = TestClient(app)

        assets_response = client.get(f"/v1/projects/{response.project_id}/assets")
        asset_response = client.get(f"/v1/assets/{asset_id}")
        designs_response = client.get(f"/v1/projects/{response.project_id}/designs")
        design_response = client.get(f"/v1/designs/{design_id}")
    finally:
        app.dependency_overrides.pop(get_optional_db, None)
        db.close()
        object.__setattr__(settings, "output_dir", original_output_dir)

    assert assets_response.status_code == 200
    assert len(assets_response.json()) == 3
    assert {asset["asset_type"] for asset in assets_response.json()} == {
        "original_upload",
        "upgraded_product",
        "design_preview",
    }
    assert asset_response.status_code == 200
    assert asset_response.json()["id"] == str(asset_id)
    assert designs_response.status_code == 200
    assert len(designs_response.json()) == 1
    assert designs_response.json()[0]["status"] == "rendered"
    assert design_response.status_code == 200
    assert design_response.json()["id"] == str(design_id)
    assert design_response.json()["design_payload"]["metadata"]["preview_url"]


def test_assets_and_designs_api_returns_503_without_db():
    def override_db():
        yield None

    app.dependency_overrides[get_optional_db] = override_db
    client = TestClient(app)

    try:
        assets_response = client.get("/v1/projects/00000000-0000-0000-0000-000000000000/assets")
        designs_response = client.get("/v1/projects/00000000-0000-0000-0000-000000000000/designs")
    finally:
        app.dependency_overrides.pop(get_optional_db, None)

    assert assets_response.status_code == 503
    assert designs_response.status_code == 503

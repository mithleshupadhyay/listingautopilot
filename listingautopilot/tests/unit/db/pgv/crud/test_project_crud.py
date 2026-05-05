from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from listingautopilot.api.generation import generate_listing_pack
from listingautopilot.config import settings
from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.crud.projects import list_recent_projects, load_project_details
from listingautopilot.db.pgv.db import Base
from listingautopilot.db.pgv.models import Project
from listingautopilot.schemas.request import GenerateRequest


def test_generation_result_is_saved_with_project_children(tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path)
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        response = generate_listing_pack(
            request=GenerateRequest(
                product_name="Travel Organizer",
                brand_name="Packwise",
                category="Travel",
                target_customer="frequent travelers",
                image_filename="travel-organizer.jpg",
                image_content_type="image/jpeg",
                image_bytes=b"fake-image",
                llm_provider="demo",
                use_demo_mode=True,
                save_to_db=True,
            ),
            db=db,
            user_context=UserContext(id="user-1", customer_id="customer-1"),
        )

        projects = list_recent_projects(db=db, customer_id="customer-1", limit=5)
        saved_project = db.query(Project).first()
        loaded_project = load_project_details(db=db, project_id=saved_project.id)
    finally:
        db.close()
        object.__setattr__(settings, "output_dir", original_output_dir)

    assert response.project_id is not None
    assert len(projects) == 1
    assert projects[0].status == "completed"
    assert projects[0].score_payload["overall"] == response.score.overall
    assert len(loaded_project.assets) == 1
    assert len(loaded_project.image_assets) == 3
    assert len(loaded_project.creative_packs) == 1
    assert len(loaded_project.design_specs) == 1
    assert len(loaded_project.editable_designs) == 1
    assert len(loaded_project.exports) == 2
    assert len(loaded_project.provider_runs) == 1

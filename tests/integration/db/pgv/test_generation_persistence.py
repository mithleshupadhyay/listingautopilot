from pathlib import Path
from uuid import UUID

from listingautopilot.api.generation import generate_listing_pack
from listingautopilot.config import settings
from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.models import (
    CreativePack,
    DesignSpec,
    EditableDesign,
    ExportArtifact,
    GenerationJob,
    ImageAsset,
    Project,
    ProviderRun,
    UploadedAsset,
)
from listingautopilot.schemas.request import GenerateRequest


def test_generation_pipeline_persists_complete_project_graph(
    db_session,
    integration_output_dir,
    sample_product_image_bytes,
):
    response = generate_listing_pack(
        request=GenerateRequest(
            product_name="Eco Bottle",
            brand_name="Acme",
            category="Kitchen",
            target_customer="office workers",
            image_filename="eco-bottle.png",
            image_content_type="image/png",
            image_bytes=sample_product_image_bytes,
            llm_provider="demo",
            use_demo_mode=True,
            save_to_db=True,
        ),
        db=db_session,
        user_context=UserContext(
            id=settings.default_user_id,
            customer_id=settings.default_customer_id,
        ),
    )

    project_id = UUID(response.project_id or "")
    project = db_session.query(Project).filter(Project.id == project_id).one()
    jobs = db_session.query(GenerationJob).filter(GenerationJob.project_id == project.id).all()
    uploaded_assets = (
        db_session.query(UploadedAsset)
        .filter(UploadedAsset.project_id == project.id)
        .all()
    )
    image_assets = (
        db_session.query(ImageAsset)
        .filter(ImageAsset.project_id == project.id)
        .all()
    )
    editable_designs = (
        db_session.query(EditableDesign)
        .filter(EditableDesign.project_id == project.id)
        .all()
    )
    creative_packs = (
        db_session.query(CreativePack)
        .filter(CreativePack.project_id == project.id)
        .all()
    )
    design_specs = (
        db_session.query(DesignSpec)
        .filter(DesignSpec.project_id == project.id)
        .all()
    )
    export_artifacts = (
        db_session.query(ExportArtifact)
        .filter(ExportArtifact.project_id == project.id)
        .all()
    )
    provider_runs = (
        db_session.query(ProviderRun)
        .filter(ProviderRun.project_id == project.id)
        .all()
    )

    assert project.name == "Eco Bottle"
    assert project.status == "completed"
    assert project.response_payload["request_id"] == response.request_id
    assert project.score_payload["overall"] == response.score.overall

    assert len(jobs) == 1
    assert jobs[0].status == "completed"
    assert jobs[0].progress_percent == 100
    assert jobs[0].job_metadata["stage"] == "generation_completed"

    assert len(uploaded_assets) == 1
    assert uploaded_assets[0].file_name == "eco-bottle.png"
    assert uploaded_assets[0].content_type == "image/png"

    assert len(image_assets) == 3
    assert {asset.asset_type for asset in image_assets} == {
        "original_upload",
        "upgraded_product",
        "design_preview",
    }
    for asset in image_assets:
        assert asset.customer_id == settings.default_customer_id
        assert asset.storage_path
        assert Path(asset.storage_path).exists()

    upgraded_asset = next(
        asset for asset in image_assets if asset.asset_type == "upgraded_product"
    )
    preview_asset = next(
        asset for asset in image_assets if asset.asset_type == "design_preview"
    )
    assert upgraded_asset.width == 2000
    assert upgraded_asset.height == 2000
    assert preview_asset.width == 2000
    assert preview_asset.height == 2000

    assert len(editable_designs) == 1
    assert editable_designs[0].preview_asset_id == preview_asset.id
    assert editable_designs[0].status == "rendered"
    assert editable_designs[0].design_payload["metadata"]["preview_url"]

    assert len(creative_packs) == 1
    assert creative_packs[0].data["amazon_title"]
    assert len(design_specs) == 1
    assert design_specs[0].data["canvas"]["width"] == 2000

    assert {artifact.export_type for artifact in export_artifacts} == {
        "markdown",
        "design_json",
    }
    assert len(provider_runs) == 1
    assert provider_runs[0].provider_type == "demo"
    assert provider_runs[0].mode == "demo"
    assert provider_runs[0].success is True
    assert provider_runs[0].provider_metadata["request_id"] == response.request_id

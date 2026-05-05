"""Generation API and orchestration service."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from listingautopilot.analysis.creative_planner import plan_creative_pack
from listingautopilot.analysis.design_json_builder import build_design_json
from listingautopilot.analysis.listing_scorer import score_listing
from listingautopilot.analysis.product_analyzer import analyze_product
from listingautopilot.config import settings as app_settings
from listingautopilot.core.config import settings
from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.crud.assets import create_image_asset
from listingautopilot.db.pgv.crud.designs import create_editable_design
from listingautopilot.db.pgv.crud.projects import create_project, update_project_status
from listingautopilot.db.pgv.schemas.assets import ImageAssetCreate, ImageAssetTypeEnum
from listingautopilot.db.pgv.schemas.designs import (
    DesignTypeEnum,
    EditableDesignCreate,
    EditableDesignStatusEnum,
)
from listingautopilot.db.pgv.schemas.projects import ProjectCreate, ProjectStatusEnum
from listingautopilot.exporters.design_json import export_design_json
from listingautopilot.exporters.markdown import export_markdown_report
from listingautopilot.image.design_renderer import get_image_size, render_design_preview
from listingautopilot.image.upgrade_pipeline import upgrade_image
from listingautopilot.logging import get_logger
from listingautopilot.llm.providers import build_llm_client
from listingautopilot.schemas.request import GenerateRequest
from listingautopilot.schemas.response import ExportBundle, GenerateResponse

from .dependencies import get_optional_db


router = APIRouter(prefix="/v1", tags=["generation"])
logger = get_logger(__name__)


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    image: UploadFile = File(...),
    product_name: str | None = Form(default=None),
    brand_name: str | None = Form(default=None),
    category: str | None = Form(default=None),
    target_customer: str | None = Form(default=None),
    brand_tone: str = Form(default="clear, premium, Amazon-friendly"),
    amazon_listing_url: str | None = Form(default=None),
    competitor_url: str | None = Form(default=None),
    llm_provider: str = Form(default="demo"),
    use_demo_mode: bool = Form(default=False),
    save_to_db: bool = Form(default=False),
    db: Session | None = Depends(get_optional_db),
) -> GenerateResponse:
    image_bytes = await image.read()
    if not image_bytes:
        logger.warning("Generate API rejected empty image upload filename=%s", image.filename)
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        logger.warning(
            "Generate API rejected large image upload filename=%s size_bytes=%s max_bytes=%s",
            image.filename,
            len(image_bytes),
            max_bytes,
        )
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded image is larger than {settings.MAX_UPLOAD_MB}MB.",
        )

    request = GenerateRequest(
        product_name=product_name,
        brand_name=brand_name,
        category=category,
        target_customer=target_customer,
        brand_tone=brand_tone,
        amazon_listing_url=amazon_listing_url,
        competitor_url=competitor_url,
        image_filename=image.filename or "uploaded-product.jpg",
        image_content_type=image.content_type or "application/octet-stream",
        image_bytes=image_bytes,
        llm_provider=llm_provider,
        use_demo_mode=use_demo_mode,
        save_to_db=save_to_db,
    )
    return generate_listing_pack(
        request=request,
        db=db,
        user_context=UserContext(
            id=settings.DEFAULT_USER_ID,
            customer_id=settings.DEFAULT_CUSTOMER_ID,
        ),
    )


# --- GENERATE LISTING PACK ---
def generate_listing_pack(
    request: GenerateRequest,
    db: Session | None = None,
    user_context: UserContext | None = None,
) -> GenerateResponse:
    warnings: list[str] = []
    request_id = f"req_{uuid4().hex[:12]}"
    logger.info(
        "Generation started request_id=%s provider=%s save_to_db=%s filename=%s",
        request_id,
        request.llm_provider,
        request.save_to_db,
        request.image_filename,
    )
    context = {
        "product_name": request.product_name,
        "brand_name": request.brand_name,
        "category": request.category,
        "target_customer": request.target_customer,
        "brand_tone": request.brand_tone,
        "amazon_listing_url": request.amazon_listing_url,
        "competitor_url": request.competitor_url,
    }

    project = None
    active_user_context = user_context or UserContext(
        id=app_settings.default_user_id,
        customer_id=app_settings.default_customer_id,
    )
    if db is not None and request.save_to_db:
        project = create_project(
            user_context=active_user_context,
            db=db,
            obj_in=ProjectCreate(
                name=request.product_name or request.image_filename,
                brand_name=request.brand_name,
                product_name=request.product_name,
                category=request.category,
                request_payload={
                    "request_id": request_id,
                    "image_filename": request.image_filename,
                    "image_content_type": request.image_content_type,
                    "llm_provider": request.llm_provider,
                    "use_demo_mode": request.use_demo_mode,
                },
            ),
        )
        logger.info("Project created for generation request_id=%s project_id=%s", request_id, project.id)

    try:
        llm_client = build_llm_client(
            provider_type=request.llm_provider,
            allow_demo_fallback=True,
        )
        llm_provider = llm_client.provider_type.value
        llm_model = llm_client.config.model
        if llm_provider == "demo" and request.llm_provider != "demo":
            warnings.append(
                f"{request.llm_provider} was not configured; demo LLM provider was used."
            )
            logger.warning(
                "LLM provider fallback request_id=%s requested=%s selected=%s",
                request_id,
                request.llm_provider,
                llm_provider,
            )

        product = analyze_product(
            llm_client=llm_client,
            image_bytes=request.image_bytes,
            image_filename=request.image_filename,
            context=context,
        )
        images = upgrade_image(
            image_bytes=request.image_bytes,
            image_filename=request.image_filename,
            image_content_type=request.image_content_type,
            provider_type=llm_provider,
            context=context,
            use_demo_mode=request.use_demo_mode,
        )
        if images.provider == "demo" and request.llm_provider != "demo":
            if images.metadata.get("fallback_from"):
                warnings.append(
                    f"{images.metadata.get('fallback_from')} image provider failed; "
                    f"local demo image upgrade was used. Reason: "
                    f"{images.metadata.get('fallback_reason', 'not provided')}"
                )
            else:
                warnings.append(
                    "The selected LLM improved the analysis and design JSON; the image upgrade is still "
                    "using the local demo image provider."
                )
        creative_pack = plan_creative_pack(
            llm_client=llm_client,
            product_analysis=product,
            context=context,
        )
        score = score_listing(
            product_analysis=product,
            creative_pack=creative_pack,
            image_provider=images.provider,
        )
        design_spec = build_design_json(
            llm_client=llm_client,
            creative_pack=creative_pack,
            upgraded_image_ref=images.upgraded_url,
        )
        images.design_preview_url = render_design_preview(design_spec)
        logger.info(
            "Visual outputs created request_id=%s upgraded_url=%s design_preview_url=%s",
            request_id,
            images.upgraded_url,
            images.design_preview_url,
        )
        design_spec.metadata["preview_url"] = images.design_preview_url
        design_spec.metadata["editable_output"] = "rendered-preview-plus-layer-json"
        markdown = export_markdown_report(
            product=product,
            score=score,
            creative_pack=creative_pack,
            design_spec=design_spec,
        )
        design_json = export_design_json(design_spec)

        mode = "demo" if llm_provider == "demo" and images.provider == "demo" else "mixed"
        if llm_provider != "demo" and images.provider != "demo":
            mode = "live"

        response = GenerateResponse(
            request_id=request_id,
            mode=mode,
            project_id=str(project.id) if project else None,
            llm_provider=llm_provider,
            llm_model=llm_model,
            image_provider=images.provider,
            product=product,
            score=score,
            creative_pack=creative_pack,
            images=images,
            editable_design=design_spec,
            exports=ExportBundle(markdown=markdown, design_json=design_json),
            warnings=warnings,
        )
    except Exception as exc:
        logger.exception("Generation failed request_id=%s", request_id)
        if db is not None and request.save_to_db and project is not None:
            update_project_status(
                db=db,
                project_id=project.id,
                customer_id=project.customer_id,
                status=ProjectStatusEnum.FAILED,
                response_payload={"request_id": request_id, "error": str(exc)},
                error_message=str(exc),
            )
        raise

    if db is not None and request.save_to_db and project is not None:
        update_project_status(
            db=db,
            project_id=project.id,
            customer_id=project.customer_id,
            status=ProjectStatusEnum.COMPLETED,
            response_payload=response.model_dump(mode="json"),
            score_payload=score.model_dump(mode="json"),
        )
        logger.info("Project marked completed request_id=%s project_id=%s", request_id, project.id)
        if response.images.original_url:
            width, height, size = get_image_size(response.images.original_url)
            create_image_asset(
                user_context=active_user_context,
                db=db,
                obj_in=ImageAssetCreate(
                    project_id=project.id,
                    asset_type=ImageAssetTypeEnum.ORIGINAL_UPLOAD,
                    file_name=Path(response.images.original_url).name,
                    content_type=request.image_content_type,
                    storage_path=response.images.original_url,
                    public_url=response.images.original_url,
                    width=width,
                    height=height,
                    file_size_bytes=size,
                    provider=response.images.provider,
                    asset_metadata={"request_id": request_id, "source": "upload"},
                ),
            )
            logger.info(
                "Original image asset persisted request_id=%s project_id=%s",
                request_id,
                project.id,
            )
        if response.images.upgraded_url:
            width, height, size = get_image_size(response.images.upgraded_url)
            create_image_asset(
                user_context=active_user_context,
                db=db,
                obj_in=ImageAssetCreate(
                    project_id=project.id,
                    asset_type=ImageAssetTypeEnum.UPGRADED_PRODUCT,
                    file_name=Path(response.images.upgraded_url).name,
                    content_type="image/png",
                    storage_path=response.images.upgraded_url,
                    public_url=response.images.upgraded_url,
                    width=width,
                    height=height,
                    file_size_bytes=size,
                    provider=response.images.provider,
                    asset_metadata={
                        "request_id": request_id,
                        "purpose": "amazon-ready-upgraded-product-image",
                    },
                ),
            )
            logger.info(
                "Upgraded image asset persisted request_id=%s project_id=%s",
                request_id,
                project.id,
            )
        preview_asset = None
        if response.images.design_preview_url:
            width, height, size = get_image_size(response.images.design_preview_url)
            preview_asset = create_image_asset(
                user_context=active_user_context,
                db=db,
                obj_in=ImageAssetCreate(
                    project_id=project.id,
                    asset_type=ImageAssetTypeEnum.DESIGN_PREVIEW,
                    file_name=Path(response.images.design_preview_url).name,
                    content_type="image/png",
                    storage_path=response.images.design_preview_url,
                    public_url=response.images.design_preview_url,
                    width=width,
                    height=height,
                    file_size_bytes=size,
                    provider="design_renderer",
                    asset_metadata={
                        "request_id": request_id,
                        "purpose": "canva-style-editable-listing-preview",
                    },
                ),
            )
            logger.info(
                "Design preview asset persisted request_id=%s project_id=%s",
                request_id,
                project.id,
            )
        create_editable_design(
            user_context=active_user_context,
            db=db,
            obj_in=EditableDesignCreate(
                project_id=project.id,
                name=f"{response.product.product_name} listing design",
                design_type=DesignTypeEnum.INFOGRAPHIC,
                version=response.editable_design.version,
                canvas_width=response.editable_design.canvas.width,
                canvas_height=response.editable_design.canvas.height,
                design_payload=response.editable_design.model_dump(mode="json"),
                preview_asset_id=preview_asset.id if preview_asset else None,
                status=EditableDesignStatusEnum.RENDERED
                if preview_asset
                else EditableDesignStatusEnum.DRAFT,
            ),
        )
        logger.info("Editable design persisted request_id=%s project_id=%s", request_id, project.id)

    logger.info("Generation completed request_id=%s mode=%s", request_id, response.mode)
    return response

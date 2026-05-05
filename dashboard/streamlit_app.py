"""Streamlit dashboard for Listing Autopilot."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from listingautopilot.api.generation import generate_listing_pack
from listingautopilot.config import settings
from listingautopilot.core.models.user_context import UserContext
from listingautopilot.db.pgv.crud.projects import list_recent_projects
from listingautopilot.db.pgv.db import get_sessionmaker
from listingautopilot.exceptions import ListingAutopilotError
from listingautopilot.logging import configure_logging, get_logger
from listingautopilot.llm.providers import get_available_provider_types
from listingautopilot.schemas.request import GenerateRequest


configure_logging()
logger = get_logger(__name__)

st.set_page_config(page_title="Listing Autopilot", layout="wide")
st.title("Listing Autopilot")

db = None
if settings.persistence_enabled:
    try:
        SessionLocal = get_sessionmaker()
        db = SessionLocal()
    except Exception as exc:
        logger.exception("Streamlit DB session initialization failed")
        st.sidebar.error(f"DB unavailable: {exc}")
        db = None

with st.sidebar:
    provider_values = [provider.value for provider in get_available_provider_types()]
    if "demo" not in provider_values:
        provider_values.insert(0, "demo")
    llm_provider = st.selectbox("Model provider", provider_values, index=0)
    save_to_db = st.checkbox("Save project", value=bool(db))
    if not settings.persistence_enabled:
        st.caption("DATABASE_URL not configured")

    st.divider()
    st.subheader("Recent Projects")
    if db:
        projects = list_recent_projects(
            db=db,
            customer_id=settings.default_customer_id,
            limit=6,
        )
        if projects:
            for project in projects:
                score = ""
                if project.score_payload:
                    score = f" · {project.score_payload.get('overall', '-')}/100"
                updated_at = project.updated_at
                if isinstance(updated_at, datetime):
                    updated_at = updated_at.strftime("%d %b %H:%M")
                st.caption(f"{project.name} · {project.status}{score}\n{updated_at}")
        else:
            st.caption("No saved projects yet")
    else:
        st.caption("Persistence disabled")


left, right = st.columns([0.38, 0.62], gap="large")

with left:
    uploaded_file = st.file_uploader(
        "Product photo",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
    )
    product_name = st.text_input("Product name")
    brand_name = st.text_input("Brand")
    category = st.text_input("Category")
    target_customer = st.text_input("Target customer")
    amazon_listing_url = st.text_input("Amazon listing URL")
    competitor_url = st.text_input("Competitor URL")
    brand_tone = st.text_input("Brand tone", value="clear, premium, Amazon-friendly")
    generate_clicked = st.button("Generate Creative Pack", type="primary")

    if uploaded_file:
        st.image(uploaded_file.getvalue(), caption=uploaded_file.name, width="stretch")

with right:
    if generate_clicked:
        if not uploaded_file:
            st.error("Upload a product photo first.")
        else:
            logger.info(
                "Dashboard generation requested provider=%s save_to_db=%s filename=%s",
                llm_provider,
                save_to_db,
                uploaded_file.name,
            )
            with st.spinner("Generating listing creative pack"):
                request = GenerateRequest(
                    product_name=product_name or None,
                    brand_name=brand_name or None,
                    category=category or None,
                    target_customer=target_customer or None,
                    brand_tone=brand_tone,
                    amazon_listing_url=amazon_listing_url or None,
                    competitor_url=competitor_url or None,
                    image_filename=uploaded_file.name,
                    image_content_type=uploaded_file.type or "application/octet-stream",
                    image_bytes=uploaded_file.getvalue(),
                    llm_provider=llm_provider,
                    use_demo_mode=llm_provider == "demo",
                    save_to_db=save_to_db,
                )
                try:
                    response = generate_listing_pack(
                        request=request,
                        db=db,
                        user_context=UserContext(
                            id=settings.default_user_id,
                            customer_id=settings.default_customer_id,
                        ),
                    )
                    st.session_state["last_response"] = response
                    logger.info(
                        "Dashboard generation completed request_id=%s mode=%s",
                        response.request_id,
                        response.mode,
                    )
                except ListingAutopilotError as exc:
                    st.session_state.pop("last_response", None)
                    logger.exception("Dashboard generation failed")
                    st.error(exc.message)
                    st.caption(
                        "If this happened with Gemini/OpenAI image editing, check the image model, quota, "
                        "and whether the uploaded image is a product-only photo. You can select demo mode "
                        "to continue without a live image provider."
                    )
                except Exception as exc:
                    st.session_state.pop("last_response", None)
                    logger.exception("Dashboard generation failed unexpectedly")
                    st.error(str(exc))

    response = st.session_state.get("last_response")
    if response:
        score_cols = st.columns(5)
        score_cols[0].metric("Overall", response.score.overall)
        score_cols[1].metric("Image", response.score.image_quality)
        score_cols[2].metric("Amazon", response.score.amazon_readiness)
        score_cols[3].metric("Conversion", response.score.conversion_potential)
        score_cols[4].metric("Benefits", response.score.benefit_clarity)

        st.subheader(response.product.product_name)
        st.write(response.product.description)
        st.caption(f"LLM provider: {response.llm_provider} · Image provider: {response.image_provider}")

        visual_cols = st.columns(2)
        if response.images.upgraded_url and Path(response.images.upgraded_url).exists():
            visual_cols[0].image(
                response.images.upgraded_url,
                caption="Upgraded Amazon-ready product image",
                width="stretch",
            )
        if response.images.design_preview_url and Path(response.images.design_preview_url).exists():
            visual_cols[1].image(
                response.images.design_preview_url,
                caption="Editable listing design preview",
                width="stretch",
            )

        st.subheader("Listing Copy")
        st.write(response.creative_pack.amazon_title)
        for bullet in response.creative_pack.bullets:
            st.write(f"- {bullet}")

        st.subheader("Creative Direction")
        st.write(response.creative_pack.main_image_recommendation)
        st.write(response.creative_pack.lifestyle_concept)
        st.write(response.creative_pack.infographic_headline)
        st.write(", ".join(response.creative_pack.infographic_callouts))

        st.subheader("Editable Design JSON")
        st.json(json.loads(response.exports.design_json))

        st.download_button(
            "Download Report",
            response.exports.markdown,
            file_name=f"{response.request_id}-report.md",
            mime="text/markdown",
        )
        if response.images.upgraded_url and Path(response.images.upgraded_url).exists():
            st.download_button(
                "Download Upgraded Image",
                Path(response.images.upgraded_url).read_bytes(),
                file_name=f"{response.request_id}-upgraded.png",
                mime="image/png",
            )
        if response.images.design_preview_url and Path(response.images.design_preview_url).exists():
            st.download_button(
                "Download Editable Design Preview",
                Path(response.images.design_preview_url).read_bytes(),
                file_name=f"{response.request_id}-editable-preview.png",
                mime="image/png",
            )
        st.download_button(
            "Download Design JSON",
            response.exports.design_json,
            file_name=f"{response.request_id}-design.json",
            mime="application/json",
        )

        if response.warnings:
            for warning in response.warnings:
                st.warning(warning)
    else:
        st.empty()

if db:
    db.close()

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from listingautopilot.api.dependencies import get_optional_db
from listingautopilot.config import settings
from listingautopilot.db.pgv.db import Base
from listingautopilot.db.pgv import models as _models  # noqa: F401
from listingautopilot.main import app


@pytest.fixture()
def integration_output_dir(tmp_path):
    original_output_dir = settings.output_dir
    object.__setattr__(settings, "output_dir", tmp_path / "outputs")
    try:
        yield settings.output_dir
    finally:
        object.__setattr__(settings, "output_dir", original_output_dir)


@pytest.fixture()
def integration_sessionmaker():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    try:
        yield SessionLocal
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def db_session(integration_sessionmaker):
    db = integration_sessionmaker()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client_with_db(integration_sessionmaker, integration_output_dir):
    def override_db():
        db = integration_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_optional_db] = override_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_optional_db, None)


@pytest.fixture()
def client_without_db(integration_output_dir):
    def override_db():
        yield None

    app.dependency_overrides[get_optional_db] = override_db
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_optional_db, None)


@pytest.fixture()
def sample_product_image_bytes() -> bytes:
    image = Image.new("RGB", (480, 480), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (170, 90, 310, 390),
        radius=28,
        fill=(18, 148, 136),
        outline=(15, 23, 42),
        width=4,
    )
    draw.rectangle((188, 150, 292, 260), fill=(241, 245, 249))
    draw.text((205, 182), "ECO", fill=(15, 23, 42))
    draw.text((198, 215), "BOTTLE", fill=(15, 23, 42))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()

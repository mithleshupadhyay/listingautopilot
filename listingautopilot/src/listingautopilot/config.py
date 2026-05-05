"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Listing Autopilot")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    app_env: str = os.getenv("APP_ENV", "local")
    database_url: str | None = os.getenv("DATABASE_URL")
    output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
    default_customer_id: str = os.getenv("DEFAULT_CUSTOMER_ID", "demo-customer")
    default_user_id: str = os.getenv("DEFAULT_USER_ID", "demo-user")
    allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "*")
    image_provider_timeout_seconds: int = int(os.getenv("IMAGE_PROVIDER_TIMEOUT_SECONDS", "120"))
    openai_image_model: str = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
    openai_image_size: str = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
    openai_image_quality: str = os.getenv("OPENAI_IMAGE_QUALITY", "medium")
    openai_image_output_format: str = os.getenv("OPENAI_IMAGE_OUTPUT_FORMAT", "png")
    gemini_image_model: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3-pro-image-preview")
    gemini_image_aspect_ratio: str = os.getenv("GEMINI_IMAGE_ASPECT_RATIO", "1:1")
    gemini_image_size: str = os.getenv("GEMINI_IMAGE_SIZE", "2K")

    @property
    def allowed_origins(self) -> list[str]:
        values = [
            value.strip()
            for value in self.allowed_origins_raw.split(",")
            if value and value.strip()
        ]
        return values or ["*"]

    @property
    def persistence_enabled(self) -> bool:
        return bool(self.database_url)


settings = Settings()

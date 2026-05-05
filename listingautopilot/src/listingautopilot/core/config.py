"""Core settings facade matching the service application style."""

from listingautopilot.config import settings as app_settings


class Settings:
    APP_NAME = app_settings.app_name
    APP_VERSION = app_settings.app_version
    APP_ENV = app_settings.app_env
    DATABASE_URL = app_settings.database_url
    OUTPUT_DIR = app_settings.output_dir
    MAX_UPLOAD_MB = app_settings.max_upload_mb
    DEFAULT_CUSTOMER_ID = app_settings.default_customer_id
    DEFAULT_USER_ID = app_settings.default_user_id
    IMAGE_PROVIDER_TIMEOUT_SECONDS = app_settings.image_provider_timeout_seconds
    OPENAI_IMAGE_MODEL = app_settings.openai_image_model
    OPENAI_IMAGE_SIZE = app_settings.openai_image_size
    OPENAI_IMAGE_QUALITY = app_settings.openai_image_quality
    OPENAI_IMAGE_OUTPUT_FORMAT = app_settings.openai_image_output_format
    GEMINI_IMAGE_MODEL = app_settings.gemini_image_model
    GEMINI_IMAGE_ASPECT_RATIO = app_settings.gemini_image_aspect_ratio
    GEMINI_IMAGE_SIZE = app_settings.gemini_image_size
    allowed_origins = app_settings.allowed_origins

    @property
    def persistence_enabled(self) -> bool:
        return bool(self.DATABASE_URL)


settings = Settings()

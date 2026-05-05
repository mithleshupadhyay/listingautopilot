"""LLM provider router."""

from fastapi import APIRouter

from listingautopilot.llm.providers import (
    get_available_provider_types,
    get_default_provider_settings,
    get_provider_env_keys,
    get_provider_label,
)
from listingautopilot.logging import get_logger


router = APIRouter(prefix="/v1/providers", tags=["providers"])
logger = get_logger(__name__)


@router.get("")
def list_providers() -> list[dict[str, object]]:
    providers: list[dict[str, object]] = []
    available = set(get_available_provider_types())

    for provider_settings in get_default_provider_settings():
        providers.append(
            {
                "provider_type": provider_settings.provider_type.value,
                "label": get_provider_label(provider_settings.provider_type),
                "model": provider_settings.config.model,
                "configured": provider_settings.is_configured(),
                "available": provider_settings.provider_type in available,
                "env_keys": list(get_provider_env_keys(provider_settings.provider_type)),
            }
        )

    logger.debug("Provider list returned count=%s", len(providers))
    return providers

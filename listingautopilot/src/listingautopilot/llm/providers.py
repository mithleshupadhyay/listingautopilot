"""Provider selection helpers in direct service-function style."""

from __future__ import annotations

from listingautopilot.llm.client import LLMClientError
from listingautopilot.llm.schemas import (
    AnthropicProviderConfig,
    DemoProviderConfig,
    GeminiProviderConfig,
    LLMProviderSettings,
    OpenAIProviderConfig,
    ProviderType,
)
from listingautopilot.logging import get_logger


logger = get_logger(__name__)


# --- GET ONE ---
def get_provider_label(provider_type: ProviderType | str) -> str:
    selected = ProviderType(provider_type)
    if selected == ProviderType.DEMO:
        return "Demo fallback"
    if selected == ProviderType.OPENAI:
        return "OpenAI"
    if selected == ProviderType.GEMINI:
        return "Google Gemini"
    if selected == ProviderType.ANTHROPIC:
        return "Anthropic Claude"
    return selected.value


def get_provider_env_keys(provider_type: ProviderType | str) -> tuple[str, ...]:
    selected = ProviderType(provider_type)
    if selected == ProviderType.DEMO:
        return ()
    if selected == ProviderType.OPENAI:
        return tuple(OpenAIProviderConfig.env_vars.keys())
    if selected == ProviderType.GEMINI:
        return tuple(GeminiProviderConfig.env_vars.keys())
    if selected == ProviderType.ANTHROPIC:
        return tuple(AnthropicProviderConfig.env_vars.keys())
    return ()


# --- LIST MANY ---
def get_default_provider_settings() -> list[LLMProviderSettings]:
    return [
        LLMProviderSettings.from_provider_type(ProviderType.DEMO),
        LLMProviderSettings.from_provider_type(ProviderType.OPENAI),
        LLMProviderSettings.from_provider_type(ProviderType.GEMINI),
        LLMProviderSettings.from_provider_type(ProviderType.ANTHROPIC),
    ]


def get_available_provider_types() -> list[ProviderType]:
    available: list[ProviderType] = []
    for settings in get_default_provider_settings():
        if settings.is_configured():
            available.append(settings.provider_type)

    if ProviderType.DEMO not in available:
        available.insert(0, ProviderType.DEMO)

    logger.debug("Available LLM providers: %s", [provider.value for provider in available])
    return available


# --- BUILD CLIENT SETTINGS ---
def build_llm_client(
    settings: LLMProviderSettings | None = None,
    *,
    provider_type: ProviderType | str | None = None,
    allow_demo_fallback: bool = True,
) -> LLMProviderSettings:
    if settings is None:
        settings = LLMProviderSettings.from_provider_type(
            provider_type or ProviderType.DEMO
        )

    if not settings.is_configured():
        if allow_demo_fallback:
            logger.warning(
                "Provider %s is not configured; falling back to demo provider",
                settings.provider_type.value,
            )
            return LLMProviderSettings(
                provider_type=ProviderType.DEMO,
                config=DemoProviderConfig(),
            )
        logger.error("Provider %s is not configured", settings.provider_type.value)
        raise LLMClientError(
            f"{settings.provider_type.value} provider is not configured"
        )

    logger.info(
        "Using LLM provider=%s model=%s",
        settings.provider_type.value,
        settings.config.model,
    )
    return settings

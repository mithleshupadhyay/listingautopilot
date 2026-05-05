"""Typed LLM provider schemas and structured output models."""

from __future__ import annotations

import os
from enum import Enum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator


class ProviderType(str, Enum):
    """Supported text/vision model providers."""

    DEMO = "demo"
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class ProviderParams(BaseModel):
    """Common generation parameters across providers."""

    temperature: float = Field(default=0.2, ge=0, le=2)
    max_tokens: int = Field(default=1400, ge=1, le=8000)
    top_p: float | None = Field(default=None, ge=0, le=1)
    extra: dict[str, Any] = Field(default_factory=dict)


class BaseLLMProviderConfig(BaseModel):
    """Base provider config with explicit environment loading support."""

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    model: str = Field(..., min_length=1)
    api_key: SecretStr | None = None
    endpoint: str | None = None
    params: ProviderParams = Field(default_factory=ProviderParams)

    env_vars: ClassVar[dict[str, str]] = {}

    def load_from_env(self) -> "BaseLLMProviderConfig":
        """Populate mapped fields from environment variables.

        The method mutates and returns self, matching the ergonomics of the
        provider configs used in larger service codebases while keeping this
        project independent.
        """
        env_lower_map = {key.lower(): value for key, value in os.environ.items()}
        for env_name, field_name in self.env_vars.items():
            value = os.getenv(env_name)
            if value is None:
                value = env_lower_map.get(env_name.lower())
            if value is None:
                continue
            if field_name == "api_key":
                setattr(self, field_name, SecretStr(value))
            else:
                setattr(self, field_name, value)
        return self

    def get_env_keys(self) -> dict[str, str | None]:
        """Return env var names and current field values for diagnostics."""
        values: dict[str, str | None] = {}
        for env_name, field_name in self.env_vars.items():
            current = getattr(self, field_name, None)
            if isinstance(current, SecretStr):
                values[env_name] = "********" if current.get_secret_value() else None
            else:
                values[env_name] = current
        return values

    def is_configured(self) -> bool:
        return self.api_key is not None and bool(self.api_key.get_secret_value().strip())

    def api_key_value(self) -> str | None:
        if self.api_key is None:
            return None
        value = self.api_key.get_secret_value().strip()
        return value or None


class DemoProviderConfig(BaseLLMProviderConfig):
    type: Literal["demo"] = "demo"
    model: str = "demo-listing-autopilot"

    def is_configured(self) -> bool:
        return True


class OpenAIProviderConfig(BaseLLMProviderConfig):
    type: Literal["openai"] = "openai"
    model: str = "gpt-4o-mini"
    endpoint: str | None = None

    env_vars: ClassVar[dict[str, str]] = {
        "OPENAI_API_KEY": "api_key",
        "OPENAI_BASE_URL": "endpoint",
        "OPENAI_MODEL": "model",
    }


class GeminiProviderConfig(BaseLLMProviderConfig):
    type: Literal["gemini"] = "gemini"
    model: str = "gemini-1.5-flash"
    endpoint: str | None = None

    env_vars: ClassVar[dict[str, str]] = {
        "GEMINI_API_KEY": "api_key",
        "GEMINI_API_BASE": "endpoint",
        "GEMINI_MODEL": "model",
    }


class AnthropicProviderConfig(BaseLLMProviderConfig):
    type: Literal["anthropic"] = "anthropic"
    model: str = "claude-3-5-haiku-latest"
    endpoint: str | None = None
    anthropic_version: str = "2023-06-01"

    env_vars: ClassVar[dict[str, str]] = {
        "ANTHROPIC_API_KEY": "api_key",
        "ANTHROPIC_API_BASE": "endpoint",
        "ANTHROPIC_MODEL": "model",
    }


ProviderConfig = Annotated[
    DemoProviderConfig | OpenAIProviderConfig | GeminiProviderConfig | AnthropicProviderConfig,
    Field(discriminator="type"),
]


class LLMProviderSettings(BaseModel):
    """Provider wrapper that keeps provider enum and config in sync."""

    provider_type: ProviderType
    name: str | None = None
    config: ProviderConfig

    @model_validator(mode="after")
    def check_type_matches_config(self) -> "LLMProviderSettings":
        if self.provider_type.value != self.config.type:
            raise ValueError(
                f"config.type={self.config.type!r} does not match provider_type={self.provider_type.value!r}"
            )
        if not self.name:
            self.name = self.config.model
        return self

    @classmethod
    def from_provider_type(cls, provider_type: ProviderType | str) -> "LLMProviderSettings":
        selected = ProviderType(provider_type)
        config_map: dict[ProviderType, ProviderConfig] = {
            ProviderType.DEMO: DemoProviderConfig(),
            ProviderType.OPENAI: OpenAIProviderConfig().load_from_env(),
            ProviderType.GEMINI: GeminiProviderConfig().load_from_env(),
            ProviderType.ANTHROPIC: AnthropicProviderConfig().load_from_env(),
        }
        return cls(provider_type=selected, config=config_map[selected])

    def is_configured(self) -> bool:
        return self.config.is_configured()


class ProductAnalysisDraft(BaseModel):
    """Structured product understanding from the selected LLM."""

    product_name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    visible_features: list[str] = Field(default_factory=list)
    likely_use_cases: list[str] = Field(default_factory=list)
    target_customer: str = Field(..., min_length=1)
    visual_issues: list[str] = Field(default_factory=list)
    selling_angles: list[str] = Field(default_factory=list)

    @field_validator(
        "visible_features",
        "likely_use_cases",
        "visual_issues",
        "selling_angles",
        mode="after",
    )
    @classmethod
    def strip_empty_items(cls, values: list[str]) -> list[str]:
        return [item.strip() for item in values if item and item.strip()]


class CreativePackDraft(BaseModel):
    """Amazon-focused listing copy and creative direction."""

    amazon_title: str = Field(..., min_length=1)
    bullets: list[str] = Field(..., min_length=3, max_length=8)
    benefits: list[str] = Field(..., min_length=3, max_length=8)
    pain_points: list[str] = Field(..., min_length=3, max_length=8)
    purchase_criteria: list[str] = Field(..., min_length=5, max_length=10)
    main_image_recommendation: str = Field(..., min_length=1)
    lifestyle_concept: str = Field(..., min_length=1)
    infographic_headline: str = Field(..., min_length=1)
    infographic_callouts: list[str] = Field(..., min_length=3, max_length=6)
    a_plus_sections: list[str] = Field(default_factory=list)


class DesignLayerDraft(BaseModel):
    """Provider-generated editable design layer."""

    id: str = Field(..., min_length=1)
    type: Literal["image", "text", "badge", "shape"]
    name: str = Field(..., min_length=1)
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    rotation: int = 0
    opacity: float = Field(default=1.0, ge=0, le=1)
    text: str | None = None
    image_ref: str | None = None
    style: dict[str, Any] = Field(default_factory=dict)

    @field_validator("style", mode="before")
    @classmethod
    def normalize_style_keys(cls, value: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(value, dict):
            return {}

        style = dict(value)
        aliases = {
            "fontSize": "font_size",
            "fontWeight": "font_weight",
            "fontFamily": "font_family",
            "backgroundColor": "fill",
            "background_color": "fill",
            "borderRadius": "radius",
            "textAlign": "text_align",
        }
        for source_key, target_key in aliases.items():
            if source_key in style and target_key not in style:
                style[target_key] = style[source_key]

        for number_key in ("font_size", "radius", "padding"):
            raw_value = style.get(number_key)
            if isinstance(raw_value, str):
                normalized = raw_value.strip().lower().replace("px", "")
                if normalized.isdigit():
                    style[number_key] = int(normalized)

        return style


class CanvasDraft(BaseModel):
    width: int = Field(default=2000, gt=0)
    height: int = Field(default=2000, gt=0)
    background: str = "#ffffff"


class DesignSpecDraft(BaseModel):
    """Editable design JSON candidate returned by LLM or demo provider."""

    version: str = "1.0"
    canvas: CanvasDraft = Field(default_factory=CanvasDraft)
    layers: list[DesignLayerDraft] = Field(..., min_length=4)
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_layer_bounds(self) -> "DesignSpecDraft":
        for layer in self.layers:
            if layer.x + layer.width > self.canvas.width:
                raise ValueError(f"Layer {layer.id!r} exceeds canvas width")
            if layer.y + layer.height > self.canvas.height:
                raise ValueError(f"Layer {layer.id!r} exceeds canvas height")
        return self


class LLMUsage(BaseModel):
    provider: ProviderType
    model: str
    live: bool
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None

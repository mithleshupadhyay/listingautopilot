import pytest
from pydantic import ValidationError

from listingautopilot.llm import (
    LLMProviderSettings,
    OpenAIProviderConfig,
    ProductAnalysisDraft,
    ProviderType,
    analyze_product_image,
    build_llm_client,
    generate_creative_pack,
    generate_design_spec,
    get_available_provider_types,
)
from listingautopilot.llm.schemas import DemoProviderConfig


def test_provider_config_type_must_match_provider_type():
    with pytest.raises(ValidationError):
        LLMProviderSettings(
            provider_type=ProviderType.OPENAI,
            config=DemoProviderConfig(),
        )


def test_openai_config_loads_from_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")

    settings = LLMProviderSettings.from_provider_type(ProviderType.OPENAI)

    assert settings.provider_type == ProviderType.OPENAI
    assert settings.config.model == "gpt-test"
    assert settings.is_configured()
    assert settings.config.get_env_keys()["OPENAI_API_KEY"] == "********"


def test_demo_provider_is_always_available(monkeypatch):
    for key in ["OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    assert ProviderType.DEMO in get_available_provider_types()


def test_build_client_falls_back_to_demo_when_provider_missing(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = LLMProviderSettings(
        provider_type=ProviderType.OPENAI,
        config=OpenAIProviderConfig(),
    )

    client = build_llm_client(settings, allow_demo_fallback=True)

    assert client.provider_type == ProviderType.DEMO
    assert client.config.model == "demo-listing-autopilot"


def test_demo_provider_functions_return_valid_structured_outputs():
    client = LLMProviderSettings.from_provider_type(ProviderType.DEMO)
    analysis = analyze_product_image(
        llm_client=client,
        image_bytes=b"fake image",
        image_filename="steel-bottle.jpg",
        context={"product_name": "Steel Bottle", "category": "Kitchen"},
    )
    creative = generate_creative_pack(
        llm_client=client,
        product_analysis=analysis,
        context={},
    )
    design = generate_design_spec(
        llm_client=client,
        creative_pack=creative,
        upgraded_image_ref="outputs/upgraded.png",
    )

    assert isinstance(analysis, ProductAnalysisDraft)
    assert analysis.product_name == "Steel Bottle"
    assert len(creative.purchase_criteria) >= 5
    assert len(design.layers) >= 4
    assert any(layer.type == "image" for layer in design.layers)


def test_secret_values_are_not_dumped_plaintext(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-key")
    config = OpenAIProviderConfig().load_from_env()

    dumped = config.model_dump()

    assert dumped["api_key"] != "secret-key"

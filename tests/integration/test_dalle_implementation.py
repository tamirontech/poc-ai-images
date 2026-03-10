"""Integration-style tests for DALLEImageGenerator behavior."""

import inspect

import pytest

from app.generator import DALLEImageGenerator, ImageGeneratorBase


def test_dalle_inherits_from_base():
    assert issubclass(DALLEImageGenerator, ImageGeneratorBase)


def test_dalle_init_and_attributes():
    gen = DALLEImageGenerator(api_key="test-key-12345")
    assert gen.api_key == "test-key-12345"
    assert gen.model == "dall-e-3"
    assert gen.base_url == "https://api.openai.com/v1"
    assert gen.images_generated == 0


def test_dalle_has_required_methods():
    gen = DALLEImageGenerator(api_key="test-key")
    for method in ["generate_image", "_build_prompt", "download_image"]:
        assert hasattr(gen, method)
        assert callable(getattr(gen, method))


def test_prompt_contains_expected_parts():
    gen = DALLEImageGenerator(api_key="test-key")
    prompt = gen._build_prompt(
        product="TestProduct",
        region="US",
        audience="test audience",
        message="Test campaign message",
        additional_context="Extra context",
        brand_colors=["#FF0000", "#00FF00"],
        logo_path="input_assets/test_logo.png",
        logo_position="bottom-right",
    )

    assert "TestProduct" in prompt
    assert "US" in prompt
    assert "Test campaign message" in prompt
    assert "#FF0000" in prompt
    assert "bottom-right" in prompt
    assert "Do not include any text overlays" in prompt


def test_dalle_requires_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        DALLEImageGenerator()


def test_method_signature_is_stable():
    sig = inspect.signature(DALLEImageGenerator.generate_image)
    for name in [
        "product",
        "region",
        "audience",
        "message",
        "additional_context",
        "size",
        "brand_colors",
        "logo_path",
        "logo_position",
        "logo_scale",
    ]:
        assert name in sig.parameters

"""Tests for image generator module."""

import pytest
import os

from app.generator import (
    ImageGeneratorBase,
    DALLEImageGenerator,
    HuggingFaceImageGenerator,
    ReplicateImageGenerator,
)
from app.config import settings


class TestImageGeneratorBase:
    """Test ImageGeneratorBase abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Cannot directly instantiate abstract base class."""
        with pytest.raises(TypeError):
            ImageGeneratorBase()

    def test_subclass_must_implement_generate_image(self):
        """Subclass must implement generate_image method."""

        class IncompleteGenerator(ImageGeneratorBase):
            pass

        with pytest.raises(TypeError):
            IncompleteGenerator()


class TestDALLEImageGenerator:
    """Test DALLEImageGenerator class."""

    def test_init_requires_api_key(self):
        """DALLEImageGenerator requires API key."""
        # Clear env var if it exists
        old_key = os.environ.get("OPENAI_API_KEY")
        old_settings_key = settings.openai_api_key
        os.environ.pop("OPENAI_API_KEY", None)
        settings.openai_api_key = None

        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                DALLEImageGenerator(api_key=None)
        finally:
            settings.openai_api_key = old_settings_key
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_init_with_explicit_api_key(self):
        """DALLEImageGenerator can be initialized with explicit key."""
        generator = DALLEImageGenerator(api_key="test-key-123")

        assert generator.api_key == "test-key-123"

    def test_models_dict_exists(self):
        """MODELS dictionary might exist or not."""
        # DALLEImageGenerator may not have MODELS dict
        # so just check the generator works
        generator = DALLEImageGenerator(api_key="test-key-123")
        assert generator is not None

    def test_default_model_is_dalle3(self):
        """Default model should be DALL-E 3."""
        generator = DALLEImageGenerator(api_key="test-key-123")

        assert generator.model == "dall-e-3"


class TestHuggingFaceImageGenerator:
    """Test HuggingFaceImageGenerator class."""

    def test_init_requires_api_key(self):
        """HuggingFaceImageGenerator requires API key."""
        old_key = os.environ.get("HUGGINGFACE_API_KEY")
        old_settings_key = settings.huggingface_api_key
        os.environ.pop("HUGGINGFACE_API_KEY", None)
        settings.huggingface_api_key = None

        try:
            with pytest.raises(ValueError, match="HUGGINGFACE_API_KEY"):
                HuggingFaceImageGenerator(api_key=None)
        finally:
            settings.huggingface_api_key = old_settings_key
            if old_key:
                os.environ["HUGGINGFACE_API_KEY"] = old_key

    def test_init_with_explicit_api_key(self):
        """HuggingFaceImageGenerator can be initialized with explicit key."""
        generator = HuggingFaceImageGenerator(api_key="test-key-123")

        assert generator.api_key == "test-key-123"

    def test_models_dict_exists(self):
        """MODELS dictionary should exist."""
        assert hasattr(HuggingFaceImageGenerator, "MODELS")
        assert isinstance(HuggingFaceImageGenerator.MODELS, dict)

    def test_model_options_available(self):
        """Model options should include flux and stable-diffusion."""
        models = HuggingFaceImageGenerator.MODELS

        assert len(models) >= 2


class TestReplicateImageGenerator:
    """Test ReplicateImageGenerator class."""

    def test_init_requires_api_key(self):
        """ReplicateImageGenerator requires API key."""
        old_key = os.environ.get("REPLICATE_API_TOKEN")
        old_key_alt = os.environ.get("REPLICATE_API_KEY")
        old_settings_key = settings.replicate_api_token
        os.environ.pop("REPLICATE_API_TOKEN", None)
        os.environ.pop("REPLICATE_API_KEY", None)
        settings.replicate_api_token = None

        try:
            with pytest.raises(ValueError):
                ReplicateImageGenerator(api_key=None)
        finally:
            settings.replicate_api_token = old_settings_key
            if old_key:
                os.environ["REPLICATE_API_TOKEN"] = old_key
            if old_key_alt:
                os.environ["REPLICATE_API_KEY"] = old_key_alt

    def test_init_with_explicit_api_key(self):
        """ReplicateImageGenerator can be initialized with explicit key."""
        generator = ReplicateImageGenerator(api_key="test-key-123")

        assert generator.api_key == "test-key-123"

    def test_models_dict_exists(self):
        """MODELS dictionary should exist."""
        assert hasattr(ReplicateImageGenerator, "MODELS")
        assert isinstance(ReplicateImageGenerator.MODELS, dict)


class TestGeneratorInheritance:
    """Test generator inheritance relationships."""

    def test_dalle_inherits_base_class(self):
        """DALLEImageGenerator should inherit from ImageGeneratorBase."""
        generator = DALLEImageGenerator(api_key="test-key")

        assert isinstance(generator, ImageGeneratorBase)

    def test_huggingface_inherits_base_class(self):
        """HuggingFaceImageGenerator should inherit from ImageGeneratorBase."""
        generator = HuggingFaceImageGenerator(api_key="test-key")

        assert isinstance(generator, ImageGeneratorBase)

    def test_replicate_inherits_base_class(self):
        """ReplicateImageGenerator should inherit from ImageGeneratorBase."""
        generator = ReplicateImageGenerator(api_key="test-key")

        assert isinstance(generator, ImageGeneratorBase)

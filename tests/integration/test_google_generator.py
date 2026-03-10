"""Tests for Google Gemini image generator."""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.google_generator import GoogleImageGenerator


class TestGoogleGeneratorInit:
    """Test Google generator initialization."""

    @patch("app.google_generator.genai")
    def test_init_requires_api_key(self, mock_genai):
        """Google generator requires API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google API key"):
                GoogleImageGenerator()

    @patch("app.google_generator.genai")
    def test_init_with_explicit_api_key(self, mock_genai):
        """Initialize with explicit API key."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key-123")
        assert gen.api_key == "test-key-123"
        assert gen.model_code == "nano-banana-2"

    @patch("app.google_generator.genai")
    def test_init_with_env_var(self, mock_genai):
        """Initialize using environment variable."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}):
            gen = GoogleImageGenerator()
            assert gen.api_key == "env-key"

    @patch("app.google_generator.genai")
    def test_init_explicit_key_overrides_env(self, mock_genai):
        """Explicit API key overrides environment variable."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key"}):
            gen = GoogleImageGenerator(api_key="explicit-key")
            assert gen.api_key == "explicit-key"

    @patch("app.google_generator.genai")
    def test_init_with_nano_banana_2_model(self, mock_genai):
        """Initialize with Nano Banana 2 model."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(
            api_key="test-key",
            model="nano-banana-2"
        )
        assert gen.model_code == "nano-banana-2"
        assert gen.model_id == "gemini-3.1-flash-image-preview"

    @patch("app.google_generator.genai")
    def test_init_with_nano_banana_pro_model(self, mock_genai):
        """Initialize with Nano Banana Pro model."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(
            api_key="test-key",
            model="nano-banana-pro"
        )
        assert gen.model_code == "nano-banana-pro"
        assert gen.model_id == "gemini-3-pro-image-preview"

    @patch("app.google_generator.genai")
    def test_init_with_nano_banana_model(self, mock_genai):
        """Initialize with Nano Banana (2.5 Flash) model."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(
            api_key="test-key",
            model="nano-banana"
        )
        assert gen.model_code == "nano-banana"
        assert gen.model_id == "gemini-2.5-flash-image"

    @patch("app.google_generator.genai")
    def test_init_with_invalid_model(self, mock_genai):
        """Raise error for invalid model."""
        with pytest.raises(ValueError, match="Invalid model"):
            GoogleImageGenerator(api_key="test-key", model="invalid-model")

    @patch("app.google_generator.genai")
    def test_supported_aspect_ratios(self, mock_genai):
        """Supported aspect ratios are defined."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        GoogleImageGenerator(api_key="test-key")
        assert "1:1" in GoogleImageGenerator.SUPPORTED_ASPECT_RATIOS
        assert "16:9" in GoogleImageGenerator.SUPPORTED_ASPECT_RATIOS
        assert "9:16" in GoogleImageGenerator.SUPPORTED_ASPECT_RATIOS
        assert len(GoogleImageGenerator.SUPPORTED_ASPECT_RATIOS) == 14

    @patch("app.google_generator.genai")
    def test_supported_resolutions(self, mock_genai):
        """Supported resolutions are defined."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        GoogleImageGenerator(api_key="test-key")
        assert "512px" in GoogleImageGenerator.SUPPORTED_RESOLUTIONS
        assert "1K" in GoogleImageGenerator.SUPPORTED_RESOLUTIONS
        assert "2K" in GoogleImageGenerator.SUPPORTED_RESOLUTIONS
        assert "4K" in GoogleImageGenerator.SUPPORTED_RESOLUTIONS

    def test_init_without_google_genai_package(self):
        """Raise error when google-genai not installed."""
        with patch("app.google_generator.genai", None):
            with pytest.raises(ImportError, match="google-genai"):
                GoogleImageGenerator(api_key="test-key")


class TestGoogleImageGeneration:
    """Test image generation."""

    @patch("app.google_generator.genai")
    def test_generate_image_success(self, mock_genai):
        """Generate image successfully."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")

        # Mock client and response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_inline_data = MagicMock()

        # Set up the response structure
        mock_part.inline_data = mock_inline_data
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response
        gen.client = mock_client

        result = gen.generate_image(
            product="Test Product",
            region="US",
            audience="Tech enthusiasts",
            message="Innovative solution",
        )

        assert result == "https://gemini-generated.example.com/image"
        assert gen.images_generated == 1

    @patch("app.google_generator.genai")
    def test_generate_image_with_aspect_ratio(self, mock_genai):
        """Generate image with custom aspect ratio."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")

        # Mock response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()

        mock_part.inline_data = MagicMock()
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response
        gen.client = mock_client

        result = gen.generate_image(
            product="Product",
            region="US",
            audience="Audience",
            message="Message",
            size="16:9",
        )

        assert result == "https://gemini-generated.example.com/image"
        # Check that aspect ratio was set
        assert gen.aspect_ratio == "16:9"

    @patch("app.google_generator.genai")
    def test_generate_image_api_error(self, mock_genai):
        """Handle API error during generation."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")

        mock_client.models.generate_content.side_effect = Exception("API Error")
        gen.client = mock_client

        with pytest.raises(Exception, match="Google image generation failed"):
            gen.generate_image(
                product="Product",
                region="US",
                audience="Audience",
                message="Message"
            )

    @patch("app.google_generator.genai")
    def test_generate_image_no_image_in_response(self, mock_genai):
        """Handle missing image in response."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")

        # Mock empty response
        mock_response = MagicMock()
        mock_response.candidates = None
        mock_client.models.generate_content.return_value = mock_response
        gen.client = mock_client

        with pytest.raises(Exception, match="No image URL"):
            gen.generate_image(
                product="Product",
                region="US",
                audience="Audience",
                message="Message"
            )


class TestGoogleAspectRatios:
    """Test aspect ratio management."""

    @patch("app.google_generator.genai")
    def test_set_aspect_ratio_valid(self, mock_genai):
        """Set valid aspect ratio."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        gen.set_aspect_ratio("16:9")
        assert gen.aspect_ratio == "16:9"

    @patch("app.google_generator.genai")
    def test_set_aspect_ratio_invalid(self, mock_genai):
        """Raise error for invalid aspect ratio."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        with pytest.raises(ValueError, match="Invalid aspect ratio"):
            gen.set_aspect_ratio("99:99")

    @patch("app.google_generator.genai")
    def test_all_aspect_ratios_valid(self, mock_genai):
        """All defined aspect ratios are valid."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        for ratio in GoogleImageGenerator.SUPPORTED_ASPECT_RATIOS:
            gen.set_aspect_ratio(ratio)
            assert gen.aspect_ratio == ratio


class TestGoogleResolutions:
    """Test resolution management."""

    @patch("app.google_generator.genai")
    def test_set_resolution_valid(self, mock_genai):
        """Set valid resolution."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        gen.set_resolution("2K")
        assert gen.resolution == "2K"

    @patch("app.google_generator.genai")
    def test_set_resolution_invalid(self, mock_genai):
        """Raise error for invalid resolution."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        with pytest.raises(ValueError, match="Invalid resolution"):
            gen.set_resolution("8K")

    @patch("app.google_generator.genai")
    def test_all_resolutions_valid(self, mock_genai):
        """All defined resolutions are valid."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        for resolution in GoogleImageGenerator.SUPPORTED_RESOLUTIONS.keys():
            gen.set_resolution(resolution)
            assert gen.resolution == resolution


class TestGoogleInheritance:
    """Test inheritance from base generator."""

    @patch("app.google_generator.genai")
    def test_google_inherits_from_base(self, mock_genai):
        """Google generator inherits from ImageGeneratorBase."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        from app.generator import ImageGeneratorBase
        gen = GoogleImageGenerator(api_key="test-key")
        assert isinstance(gen, ImageGeneratorBase)

    @patch("app.google_generator.genai")
    def test_build_prompt_method(self, mock_genai):
        """Inherits working prompt builder."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        prompt = gen._build_prompt(
            "Nike Shoes",
            "Japan",
            "Young professionals",
            "Step into comfort"
        )

        assert "Nike Shoes" in prompt
        assert "Japan" in prompt
        assert "Young professionals" in prompt
        assert "Step into comfort" in prompt

    @patch("app.google_generator.genai")
    def test_images_generated_counter(self, mock_genai):
        """Track images generated counter."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        assert gen.images_generated == 0


class TestGoogleModels:
    """Test supported models."""

    @patch("app.google_generator.genai")
    def test_all_models_supported(self, mock_genai):
        """All defined models can be initialized."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        api_key = "test-key"
        for model_code in GoogleImageGenerator.SUPPORTED_MODELS.keys():
            gen = GoogleImageGenerator(api_key=api_key, model=model_code)
            assert gen.model_code == model_code

    @patch("app.google_generator.genai")
    def test_nano_banana_2_is_default(self, mock_genai):
        """Nano Banana 2 is default model."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key")
        assert gen.model_code == "nano-banana-2"

    @patch("app.google_generator.genai")
    def test_model_ids_correct(self, mock_genai):
        """Model IDs map correctly."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        gen = GoogleImageGenerator(api_key="test-key", model="nano-banana-2")
        assert gen.model_id == "gemini-3.1-flash-image-preview"

        gen = GoogleImageGenerator(api_key="test-key", model="nano-banana-pro")
        assert gen.model_id == "gemini-3-pro-image-preview"

        gen = GoogleImageGenerator(api_key="test-key", model="nano-banana")
        assert gen.model_id == "gemini-2.5-flash-image"

"""Google Gemini image generation with Nano Banana models."""

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.generator import ImageGeneratorBase

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GoogleImageGenerator(ImageGeneratorBase):
    """Generates images using Google Gemini's Nano Banana API.

    Supports three models:
    - Nano Banana 2 (gemini-3.1-flash-image-preview): Fast, efficient
    - Nano Banana Pro (gemini-3-pro-image-preview): Professional quality
    - Nano Banana (gemini-2.5-flash-image): Speed optimized
    """

    # Supported models
    SUPPORTED_MODELS = {
        "nano-banana-2": "gemini-3.1-flash-image-preview",
        "nano-banana-pro": "gemini-3-pro-image-preview",
        "nano-banana": "gemini-2.5-flash-image",
    }

    # Supported aspect ratios
    SUPPORTED_ASPECT_RATIOS = [
        "1:1", "1:4", "1:8", "2:3", "3:2", "3:4",
        "4:1", "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"
    ]

    # Map pipeline WxH size strings to Google aspect ratios
    WXH_TO_ASPECT_RATIO = {
        "1024x1024": "1:1",
        "1024x1792": "9:16",
        "1792x1024": "16:9",
    }

    # Supported resolutions (for 3.1 Flash and 3 Pro models)
    SUPPORTED_RESOLUTIONS = {
        "512px": "512px",
        "1K": "1K",
        "2K": "2K",
        "4K": "4K"
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "nano-banana-2",
    ):
        """Initialize Google Gemini image generator.

        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY)
            model: Model to use (nano-banana-2, nano-banana-pro, nano-banana)

        Raises:
            ImportError: If google-genai package not installed
            ValueError: If API key not provided or model invalid
        """
        super().__init__()

        if genai is None:
            raise ImportError(
                "google-genai required for Google image generation. "
                "Install with: pip install google-genai"
            )

        self.api_key = api_key or settings.google_api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter. "
                "Get key from https://aistudio.google.com/apikey"
            )

        # Validate and set model
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Invalid model: {model}. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS.keys())}"
            )

        self.model_code = model
        self.model_id = self.SUPPORTED_MODELS[model]

        # Initialize Google client with key scoped to this instance (no global state mutation)
        self.client = genai.Client(api_key=self.api_key)
        self.types = types or getattr(genai, "types", None)

        # Default configuration
        self.aspect_ratio = "1:1"
        self.resolution = "1K"

    def generate_image(
        self,
        product: str,
        region: str,
        audience: str,
        message: str,
        additional_context: str = "",
        size: str = "1024x1024",
        brand_colors: Optional[list[str]] = None,
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
        reference_image_path: Optional[str] = None,
    ) -> str:
        """Generate image using Google Gemini.

        Args:
            product: Product name for context
            region: Target region
            audience: Target audience
            message: Marketing message
            additional_context: Additional context for image generation
            size: Requested size (aspect ratio or WxH format)
            brand_colors: Brand hex colors for visual guidance
            logo_path: Path to logo file (used for prompt composition guidance)
            logo_position: Logo position for prompt composition guidance
            logo_scale: Logo scale (not used by Google request payload)
            reference_image_path: Optional local reference image path for scene/style guidance

        Returns:
            URL to generated image

        Raises:
            Exception: If image generation fails
        """
        # Build comprehensive prompt
        prompt = self._build_prompt(
            product,
            region,
            audience,
            message,
            additional_context,
            brand_colors,
            logo_path,
            logo_position,
            reference_image_path,
        )

        # Resolve size to a Google-native aspect ratio string.
        # Accept either a native ratio ("16:9") or a WxH string ("1792x1024").
        if size in self.SUPPORTED_ASPECT_RATIOS:
            self.aspect_ratio = size
        elif size in self.WXH_TO_ASPECT_RATIO:
            self.aspect_ratio = self.WXH_TO_ASPECT_RATIO[size]
        else:
            self.aspect_ratio = "1:1"

        try:
            # Generate image
            request_kwargs = {
                "model": self.model_id,
                "contents": [prompt],
            }
            if self.types is not None:
                request_kwargs["config"] = self.types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=self.types.ImageConfig(
                        aspect_ratio=self.aspect_ratio,
                        image_size=self.resolution,
                    ),
                )

            response = self.client.models.generate_content(**request_kwargs)

            # Extract image URL from response
            image_url = self._extract_image_url(response)
            if not image_url:
                raise RuntimeError("No image URL in response")

            self.images_generated += 1
            return image_url

        except Exception as e:
            raise RuntimeError(f"Google image generation failed: {e}") from e

    def _extract_image_url(self, response) -> Optional[str]:
        """Extract image URL from Google API response.

        Args:
            response: API response object

        Returns:
            Image URL if found, None otherwise
        """
        try:
            # For Google Gemini, images are returned as inline_data
            # We need to handle the response structure properly
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # Image is embedded as base64 in inline_data.data.
                                inline_data = part.inline_data
                                raw_data = getattr(inline_data, "data", None)
                                if raw_data:
                                    if isinstance(raw_data, str):
                                        image_bytes = base64.b64decode(raw_data)
                                    else:
                                        image_bytes = raw_data
                                    tmp_dir = Path("./outputs/.tmp")
                                    tmp_dir.mkdir(parents=True, exist_ok=True)
                                    temp_file = tmp_dir / f"google_image_{int(datetime.now().timestamp())}.png"
                                    with open(temp_file, "wb") as f:
                                        f.write(image_bytes)
                                    return str(temp_file)
            return None
        except Exception:
            return None

    def set_resolution(self, resolution: str) -> None:
        """Set output resolution.

        Args:
            resolution: Resolution code (512px, 1K, 2K, 4K)

        Raises:
            ValueError: If resolution not supported
        """
        if resolution not in self.SUPPORTED_RESOLUTIONS:
            raise ValueError(
                f"Invalid resolution: {resolution}. "
                f"Supported: {', '.join(self.SUPPORTED_RESOLUTIONS.keys())}"
            )
        self.resolution = resolution

    def set_aspect_ratio(self, aspect_ratio: str) -> None:
        """Set output aspect ratio.

        Args:
            aspect_ratio: Ratio like "16:9"

        Raises:
            ValueError: If ratio not supported
        """
        if aspect_ratio not in self.SUPPORTED_ASPECT_RATIOS:
            raise ValueError(
                f"Invalid aspect ratio: {aspect_ratio}. "
                f"Supported: {', '.join(self.SUPPORTED_ASPECT_RATIOS)}"
            )
        self.aspect_ratio = aspect_ratio

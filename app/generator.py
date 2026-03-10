"""Image generation service with support for multiple providers."""

import logging
import os
import random
import shutil
import time
from pathlib import Path
from typing import Optional, List, Union
import requests

from app.config import settings
from datetime import datetime
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class ImageGeneratorBase(ABC):
    """Base class for image generators."""

    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self):
        """Initialize generator."""
        self.images_generated = 0

    @abstractmethod
    def generate_image(
        self,
        product: str,
        region: str,
        audience: str,
        message: str,
        additional_context: str = "",
        size: str = "1024x1024",
        brand_colors: Optional[List[str]] = None,
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
        reference_image_path: Optional[str] = None,
    ) -> str:
        """Generate image.

        Args:
            product: Product name
            region: Target region
            audience: Target audience
            message: Campaign message
            additional_context: Additional context
            size: Image size
            brand_colors: Brand hex colors for visual guidance
            logo_path: Path to logo file (applied after generation)
            logo_position: Logo position (applied after generation)
            logo_scale: Logo scale (applied after generation)
            reference_image_path: Optional local reference image path for scene/style guidance

        Returns:
            URL or path to generated image
        """
        pass

    def download_image(self, image_url: str, output_path: str) -> str:
        """Download and save image.

        Args:
            image_url: Image URL or path
            output_path: Output file path

        Returns:
            Path to saved image
        """
        image_ref = Path(str(image_url))
        if image_ref.exists():
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(image_ref, output_path)
            return output_path

        try:
            response = self._request_with_retry("GET", image_url, timeout=30)

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(response.content)

            return output_path
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to download image: {e}") from e

    def _parse_retry_after(self, retry_after: Optional[str]) -> Optional[float]:
        """Parse Retry-After header value into seconds."""
        if not retry_after:
            return None
        try:
            seconds = float(retry_after)
            return max(0.0, seconds)
        except ValueError:
            return None

    def _compute_retry_delay(self, attempt: int, retry_after: Optional[str] = None) -> float:
        """Compute exponential backoff delay with jitter."""
        retry_after_seconds = self._parse_retry_after(retry_after)
        if retry_after_seconds is not None:
            return retry_after_seconds
        # 1.5, 3.0, 6.0 ... + jitter, capped at 30s
        base = 1.5 * (2 ** attempt)
        jitter = random.uniform(0.0, 0.5)
        return min(30.0, base + jitter)

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        timeout: Union[int, float],
        **kwargs,
    ) -> requests.Response:
        """Execute HTTP request with retry/backoff for transient failures."""
        max_retries = max(0, settings.max_retries)
        last_exception: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                response = requests.request(method, url, timeout=timeout, **kwargs)
            except requests.exceptions.RequestException as exc:
                last_exception = exc
                if attempt >= max_retries:
                    raise
                delay = self._compute_retry_delay(attempt)
                _logger.warning(
                    "Request error on attempt %d/%d, retrying in %.1fs: %s [%s]",
                    attempt + 1, max_retries + 1, delay, exc, url,
                )
                time.sleep(delay)
                continue

            if response.status_code in self.RETRYABLE_STATUS_CODES:
                if attempt >= max_retries:
                    response.raise_for_status()
                delay = self._compute_retry_delay(
                    attempt, response.headers.get("Retry-After")
                )
                _logger.warning(
                    "HTTP %d on attempt %d/%d, retrying in %.1fs [%s]",
                    response.status_code, attempt + 1, max_retries + 1, delay, url,
                )
                time.sleep(delay)
                continue

            response.raise_for_status()
            return response

        if last_exception:
            raise last_exception
        raise RuntimeError("Request failed after retries")

    def _build_prompt(
        self,
        product: str,
        region: str,
        audience: str,
        message: str,
        additional_context: str = "",
        brand_colors: Optional[List[str]] = None,
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        reference_image_path: Optional[str] = None,
    ) -> str:
        """Build optimized prompt for image generation.

        Args:
            product: Product name
            region: Target region
            audience: Target audience
            message: Campaign message
            additional_context: Additional context
            brand_colors: Brand hex colors (e.g., ['#2D5016', '#FFFFFF'])
            logo_path: Path to logo file (for spatial guidance)
            logo_position: Position where logo will be placed

        Returns:
            Optimized prompt for image generation
        """
        prompt_parts = [
            f"Create a professional, modern social media advertisement for {product}",
            f"Target market: {region}",
            f"Target audience: {audience}",
            f"Campaign message: '{message}'",
            "Style: vibrant, engaging, on-brand, high-quality",
            "Professional product photography with modern design elements",
            "Suitable for social media (Instagram, TikTok, LinkedIn, Facebook)",
        ]

        # Add brand color guidance if provided
        if brand_colors:
            colors_str = ", ".join(brand_colors)
            prompt_parts.append(f"Use brand colors prominently: {colors_str}")

        # Add logo positioning guidance if logo is being used
        if logo_path:
            prompt_parts.append(
                f"Design with {logo_position} space reserved for brand logo. "
                "Ensure visual balance and avoid crowding that area."
            )

        if reference_image_path:
            ref_name = Path(reference_image_path).name
            prompt_parts.append(
                f"Use the supplied reference image ({ref_name}) for scene composition and product styling cues."
            )

        if additional_context:
            prompt_parts.append(f"Additional context: {additional_context}")

        # Critical instruction: no text overlays (applied separately via Pillow)
        prompt_parts.append("Do not include any text overlays or captions")

        return ". ".join(prompt_parts) + "."


class DALLEImageGenerator(ImageGeneratorBase):
    """Generates images using OpenAI DALL-E API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "dall-e-3"):
        """Initialize DALL-E generator.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: DALL-E model to use (dall-e-3 or dall-e-2)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. Please set it in .env or environment variables."
            )
        self.model = model
        self.base_url = "https://api.openai.com/v1"

    def generate_image(
        self,
        product: str,
        region: str,
        audience: str,
        message: str,
        additional_context: str = "",
        size: str = "1024x1024",
        brand_colors: Optional[List[str]] = None,
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
        reference_image_path: Optional[str] = None,
    ) -> str:
        """Generate image using DALL-E API.

        Args:
            product: Product name
            region: Target region
            audience: Target audience description
            message: Campaign message
            additional_context: Additional context for image generation
            size: Image size (1024x1024, 1792x1024, etc.)
            brand_colors: Brand hex colors for visual guidance
            logo_path: Path to logo file (applied after generation)
            logo_position: Logo position (applied after generation)
            logo_scale: Logo scale (applied after generation)
            reference_image_path: Optional local reference image path for scene/style guidance

        Returns:
            URL to generated image

        Raises:
            Exception: If API call fails
        """
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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": "standard",
        }

        try:
            response = self._request_with_retry(
                "POST",
                f"{self.base_url}/images/generations",
                json=payload,
                headers=headers,
                timeout=settings.request_timeout_seconds,
            )

            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                image_url = data["data"][0]["url"]
                self.images_generated += 1
                return image_url
            else:
                raise RuntimeError("No image in response")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"DALL-E API error: {e}") from e


class HuggingFaceImageGenerator(ImageGeneratorBase):
    """Generates images using Hugging Face Inference API."""

    MODELS = {
        "stable-diffusion-3": "stabilityai/stable-diffusion-3-medium",
        "flux-dev": "black-forest-labs/FLUX.1-dev",
        "flux-schnell": "black-forest-labs/FLUX.1-schnell",
        "stable-diffusion-xl": "stabilityai/stable-diffusion-xl",
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "stable-diffusion-3"):
        """Initialize Hugging Face generator.

        Args:
            api_key: Hugging Face API key (defaults to HUGGINGFACE_API_KEY env var)
            model: Model name/key (see MODELS dict)
        """
        super().__init__()
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY") or settings.huggingface_api_key
        if not self.api_key:
            msg = (
                "HUGGINGFACE_API_KEY not set. Get a free token from "
                "https://huggingface.co/settings/tokens"
            )
            raise ValueError(msg)
        # Resolve model name to full ID
        self.model = self.MODELS.get(model, model)
        self.base_url = "https://api-inference.huggingface.co/models"

    def generate_image(
        self,
        product: str,
        region: str,
        audience: str,
        message: str,
        additional_context: str = "",
        size: str = "1024x1024",
        brand_colors: Optional[List[str]] = None,
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
        reference_image_path: Optional[str] = None,
    ) -> str:
        """Generate image using Hugging Face API.

        Args:
            product: Product name
            region: Target region
            audience: Target audience
            message: Campaign message
            additional_context: Additional context
            size: Image size (ignored for HF, uses model defaults)
            brand_colors: Brand hex colors for visual guidance
            logo_path: Path to logo file (applied after generation)
            logo_position: Logo position (applied after generation)
            logo_scale: Logo scale (applied after generation)
            reference_image_path: Optional local reference image path for scene/style guidance

        Returns:
            Path to saved image

        Raises:
            Exception: If API call fails
        """
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

        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"inputs": prompt}

        try:
            response = self._request_with_retry(
                "POST",
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=payload,
                timeout=120,
            )

            # Response is binary image data
            if response.headers.get("content-type", "").startswith("image/"):
                # Save to outputs/.tmp/ instead of /tmp/ for consistency
                tmp_dir = Path("./outputs/.tmp")
                tmp_dir.mkdir(parents=True, exist_ok=True)
                temp_file = str(tmp_dir / f"hf_image_{int(datetime.now().timestamp())}.png")
                with open(temp_file, "wb") as f:
                    f.write(response.content)
                self.images_generated += 1
                return temp_file
            else:
                raise RuntimeError(f"Unexpected response: {response.text}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Hugging Face API error: {e}") from e


class ReplicateImageGenerator(ImageGeneratorBase):
    """Generates images using Replicate API."""

    MODELS = {
        "stable-diffusion-3": "stability-ai/stable-diffusion-3",
        "flux-dev": "black-forest-labs/flux-dev",
        "flux-schnell": "black-forest-labs/flux-schnell",
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "stable-diffusion-3"):
        """Initialize Replicate generator.

        Args:
            api_key: Replicate API key/token (REPLICATE_API_TOKEN or REPLICATE_API_KEY)
            model: Model name (see MODELS dict)
        """
        super().__init__()
        self.api_key = (
            api_key
            or os.getenv("REPLICATE_API_TOKEN")
            or os.getenv("REPLICATE_API_KEY")
            or settings.replicate_api_token
        )
        if not self.api_key:
            raise ValueError(
                "Replicate API credential not set. "
                "Set REPLICATE_API_TOKEN (preferred) or REPLICATE_API_KEY."
            )
        # Resolve model name
        self.model = self.MODELS.get(model, model)
        self.base_url = "https://api.replicate.com/v1"

    def generate_image(
        self,
        product: str,
        region: str,
        audience: str,
        message: str,
        additional_context: str = "",
        size: str = "1024x1024",
        brand_colors: Optional[List[str]] = None,
        logo_path: Optional[str] = None,
        logo_position: str = "bottom-right",
        logo_scale: float = 0.15,
        reference_image_path: Optional[str] = None,
    ) -> str:
        """Generate image using Replicate API.

        Args:
            product: Product name
            region: Target region
            audience: Target audience
            message: Campaign message
            additional_context: Additional context
            size: Image size
            brand_colors: Brand hex colors for visual guidance
            logo_path: Path to logo file (applied after generation)
            logo_position: Logo position (applied after generation)
            logo_scale: Logo scale (applied after generation)
            reference_image_path: Optional local reference image path for scene/style guidance

        Returns:
            URL to generated image

        Raises:
            Exception: If API call fails
        """
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

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "version": self.model,
            "input": {
                "prompt": prompt,
                "width": int(size.split("x")[0]),
                "height": int(size.split("x")[1]),
            },
        }

        try:
            # Create prediction
            response = self._request_with_retry(
                "POST",
                f"{self.base_url}/predictions",
                headers=headers,
                json=payload,
                timeout=10,
            )

            data = response.json()
            prediction_id = data.get("id")

            if not prediction_id:
                raise RuntimeError("No prediction ID in response")

            # Poll for completion (max 5 minutes)
            max_wait = 300
            start_time = time.time()

            while time.time() - start_time < max_wait:
                response = self._request_with_retry(
                    "GET",
                    f"{self.base_url}/predictions/{prediction_id}",
                    headers=headers,
                    timeout=10,
                )

                data = response.json()
                status = data.get("status")

                if status == "succeeded":
                    output = data.get("output")
                    if isinstance(output, list) and len(output) > 0:
                        self.images_generated += 1
                        return output[0]
                    elif isinstance(output, str):
                        self.images_generated += 1
                        return output
                    else:
                        raise RuntimeError(f"Invalid output format: {output}")

                elif status == "failed":
                    raise RuntimeError(
                        f"Prediction failed: {data.get('error', 'Unknown error')}"
                    )

                # Wait before polling again
                time.sleep(2)

            raise RuntimeError(f"Prediction timed out after {max_wait} seconds")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Replicate API error: {e}") from e

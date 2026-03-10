"""Adobe Firefly image generation service with OAuth authentication."""

import os
import time
from typing import Optional

import requests

from app.config import settings
from app.generator import ImageGeneratorBase


class FireflyImageGenerator(ImageGeneratorBase):
    """Generates images using Adobe Firefly API.

    Adobe Firefly provides state-of-the-art generative AI for images.
    Supports text-to-image generation with OAuth Server-to-Server auth.
    """

    # Supported sizes for Firefly
    SUPPORTED_SIZES = {
        "1024x1024": {"width": 1024, "height": 1024},
        "1024x1536": {"width": 1024, "height": 1536},
        "1536x1024": {"width": 1536, "height": 1024},
        "2048x2048": {"width": 2048, "height": 2048},
    }

    # Adobe IMS endpoints for OAuth
    IMS_URL = "https://ims-na1.adobelogin.com/ims/token/v3"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize Firefly generator with OAuth or API key auth.

        Args:
            client_id: Adobe Client ID (defaults to FIREFLY_CLIENT_ID)
            client_secret: Adobe Client Secret (defaults to FIREFLY_CLIENT_SECRET)
            api_key: Fallback API key for simple auth (FIREFLY_API_KEY)

        Raises:
            ValueError: If no valid credentials provided
        """
        super().__init__()
        self.base_url = "https://firefly-api.adobe.io"

        # OAuth credentials
        self.client_id = (
            client_id
            or settings.firefly_client_id
            or os.getenv("FIREFLY_SERVICES_CLIENT_ID")
            or os.getenv("FIREFLY_CLIENT_ID")
        )
        self.client_secret = (
            client_secret
            or settings.firefly_client_secret
            or os.getenv("FIREFLY_SERVICES_CLIENT_SECRET")
            or os.getenv("FIREFLY_CLIENT_SECRET")
        )

        # Fallback API key
        self.api_key = api_key or settings.firefly_api_key or os.getenv("FIREFLY_API_KEY")

        # Validate credentials
        if not (self.client_id and self.client_secret) and not self.api_key:
            raise ValueError(
                "Firefly requires either OAuth credentials "
                "(FIREFLY_CLIENT_ID + FIREFLY_CLIENT_SECRET) "
                "or API key (FIREFLY_API_KEY). "
                "Get credentials from https://developer.adobe.com/console"
            )

        # OAuth token caching
        self.access_token = None
        self.token_expires_at = 0

    def _get_headers(self) -> dict:
        """Get request headers with valid authorization.

        Returns:
            Dictionary with headers including Content-Type and Authorization

        Raises:
            Exception: If unable to obtain valid credentials
        """
        headers = {"Content-Type": "application/json"}

        if self.client_id and self.client_secret:
            # Use OAuth bearer token
            token = self._get_access_token()
            headers["Authorization"] = f"Bearer {token}"
        elif self.api_key:
            # Fallback to simple API key
            headers["X-Api-Key"] = self.api_key
        else:
            raise RuntimeError("No valid Firefly credentials available")

        return headers

    def _get_access_token(self) -> str:
        """Get valid OAuth access token, refreshing if necessary.

        Returns:
            Valid access token string

        Raises:
            Exception: If unable to retrieve token from Adobe IMS
        """
        # Return cached token if still valid (with 60s buffer)
        if self.access_token and time.time() < (self.token_expires_at - 60):
            return self.access_token

        # Request new token from Adobe IMS
        try:
            response = self._request_with_retry(
                "POST",
                self.IMS_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": (
                        "openid,AdobeID,session,additional_info,"
                        "read_organizations,firefly_api,ff_apis"
                    ),
                },
                timeout=10,
            )

            data = response.json()
            self.access_token = data.get("access_token")
            expires_in = data.get("expires_in", 86400)  # Default 24 hours
            self.token_expires_at = time.time() + expires_in

            if not self.access_token:
                raise RuntimeError("No access_token in IMS response")

            return self.access_token

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get access token from Adobe IMS: {e}") from e

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
        """Generate image using Firefly API.

        Args:
            product: Product name
            region: Target region
            audience: Target audience description
            message: Campaign message
            additional_context: Additional context for image generation
            size: Image size (1024x1024, 2048x2048, etc.)
            brand_colors: Brand hex colors for visual guidance
            logo_path: Path to logo file (used for prompt composition guidance)
            logo_position: Logo position for prompt composition guidance
            logo_scale: Logo scale (not used by Firefly request payload)
            reference_image_path: Optional local reference image path for scene/style guidance

        Returns:
            URL to generated image

        Raises:
            Exception: If API call fails or job polling times out
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

        # Parse size
        if size not in self.SUPPORTED_SIZES:
            size = "1024x1024"

        size_obj = self.SUPPORTED_SIZES[size]

        # Submit async job
        job_id = self._submit_generation_job(prompt, size_obj)

        # Poll for completion (max 5 minutes)
        image_url = self._poll_job_completion(job_id, max_wait=300)

        self.images_generated += 1
        return image_url

    def _submit_generation_job(self, prompt: str, size: dict) -> str:
        """Submit an image generation job to Firefly.

        Args:
            prompt: Text prompt for image generation
            size: Dictionary with width and height

        Returns:
            Job ID for polling

        Raises:
            Exception: If job submission fails
        """
        payload = {
            "prompt": prompt,
            "n": 1,
            "size": size,
            "contentClass": "photo",
            "negativePrompt": "",
        }

        try:
            headers = self._get_headers()
            response = self._request_with_retry(
                "POST",
                f"{self.base_url}/v3/images/generate-async",
                json=payload,
                headers=headers,
                timeout=30,
            )

            data = response.json()
            job_id = data.get("jobId")

            if not job_id:
                raise RuntimeError("No job ID in response")

            return job_id

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Firefly job submission error: {e}") from e

    def _poll_job_completion(self, job_id: str, max_wait: int = 300) -> str:
        """Poll Firefly job status until completion.

        Args:
            job_id: Job ID to poll
            max_wait: Maximum wait time in seconds

        Returns:
            URL of generated image

        Raises:
            Exception: If job fails or times out
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                headers = self._get_headers()
                response = self._request_with_retry(
                    "GET",
                    f"{self.base_url}/v3/status/{job_id}",
                    headers=headers,
                    timeout=10,
                )

                data = response.json()
                status = data.get("status")

                if status == "SUCCEEDED":
                    result = data.get("result")
                    if result and "outputs" in result:
                        outputs = result["outputs"]
                        if len(outputs) > 0:
                            image_url = outputs[0].get("image", {}).get("url")
                            if image_url:
                                return image_url
                    raise RuntimeError("No image URL in result")

                elif status == "FAILED":
                    error = data.get("error", {})
                    msg = error.get("message", "Unknown error")
                    raise RuntimeError(f"Generation failed: {msg}")

                # Job still processing
                time.sleep(2)

            except requests.exceptions.RequestException as e:
                raise RuntimeError(f"Firefly status check error: {e}") from e

        raise RuntimeError(f"Job {job_id} timed out after {max_wait} seconds")

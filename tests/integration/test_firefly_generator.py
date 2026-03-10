"""Tests for Adobe Firefly image generator."""

import os
import time
import pytest
from unittest.mock import patch
import responses

from app.firefly_generator import FireflyImageGenerator


class TestFireflyGeneratorInit:
    """Test Firefly generator initialization."""

    def test_init_requires_credentials(self):
        """Firefly generator requires either OAuth or API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OAuth credentials"):
                FireflyImageGenerator()

    def test_init_with_api_key(self):
        """Initialize with API key (backward compatibility)."""
        gen = FireflyImageGenerator(api_key="test-key-123")
        assert gen.api_key == "test-key-123"
        assert gen.base_url == "https://firefly-api.adobe.io"

    def test_init_with_oauth_credentials(self):
        """Initialize with OAuth Client ID and Secret."""
        gen = FireflyImageGenerator(
            client_id="test-client-id",
            client_secret="test-client-secret"
        )
        assert gen.client_id == "test-client-id"
        assert gen.client_secret == "test-client-secret"

    def test_init_with_env_var_oauth(self):
        """Initialize using OAuth environment variables."""
        with patch.dict(os.environ, {
            "FIREFLY_CLIENT_ID": "env-client-id",
            "FIREFLY_CLIENT_SECRET": "env-client-secret"
        }):
            gen = FireflyImageGenerator()
            assert gen.client_id == "env-client-id"
            assert gen.client_secret == "env-client-secret"

    def test_init_with_adobe_ims_env_vars(self):
        """Initialize using Adobe IMS environment variables."""
        with patch.dict(os.environ, {
            "FIREFLY_SERVICES_CLIENT_ID": "adobe-client",
            "FIREFLY_SERVICES_CLIENT_SECRET": "adobe-secret"
        }):
            gen = FireflyImageGenerator()
            assert gen.client_id == "adobe-client"
            assert gen.client_secret == "adobe-secret"

    def test_init_oauth_overrides_api_key(self):
        """OAuth credentials take precedence over API key."""
        gen = FireflyImageGenerator(
            client_id="oauth-id",
            client_secret="oauth-secret",
            api_key="fallback-key"
        )
        assert gen.client_id == "oauth-id"
        assert gen.api_key == "fallback-key"

    def test_get_headers_with_api_key(self):
        """Headers for API key authentication."""
        gen = FireflyImageGenerator(api_key="test-key")
        headers = gen._get_headers()
        assert headers["X-Api-Key"] == "test-key"
        assert headers["Content-Type"] == "application/json"

    def test_supported_sizes(self):
        """Supported image sizes are defined."""
        assert "1024x1024" in FireflyImageGenerator.SUPPORTED_SIZES
        assert "2048x2048" in FireflyImageGenerator.SUPPORTED_SIZES
        assert FireflyImageGenerator.SUPPORTED_SIZES["1024x1024"] == {
            "width": 1024, "height": 1024
        }

    def test_ims_url_configured(self):
        """Adobe IMS URL is properly configured."""
        assert "ims-na1.adobelogin.com" in FireflyImageGenerator.IMS_URL
        assert "token" in FireflyImageGenerator.IMS_URL


class TestFireflyOAuthTokens:
    """Test OAuth token management."""

    @responses.activate
    def test_get_access_token_success(self):
        """Successfully retrieve access token from Adobe IMS."""
        gen = FireflyImageGenerator(
            client_id="test-id",
            client_secret="test-secret"
        )

        # Mock IMS response
        responses.add(
            responses.POST,
            "https://ims-na1.adobelogin.com/ims/token/v3",
            json={
                "access_token": "token-abc-123",
                "token_type": "bearer",
                "expires_in": 86400,
            },
            status=200,
        )

        token = gen._get_access_token()
        assert token == "token-abc-123"
        assert gen.access_token == "token-abc-123"

    @responses.activate
    def test_get_access_token_caching(self):
        """Access token is cached until expiration."""
        gen = FireflyImageGenerator(
            client_id="test-id",
            client_secret="test-secret"
        )

        responses.add(
            responses.POST,
            "https://ims-na1.adobelogin.com/ims/token/v3",
            json={
                "access_token": "token-cached",
                "expires_in": 86400,
            },
            status=200,
        )

        token1 = gen._get_access_token()
        # Second call should use cached token
        token2 = gen._get_access_token()

        assert token1 == token2
        assert len(responses.calls) == 1  # Only one API call

    @responses.activate
    def test_get_access_token_error(self):
        """Handle token retrieval error."""
        gen = FireflyImageGenerator(
            client_id="test-id",
            client_secret="test-secret"
        )

        responses.add(
            responses.POST,
            "https://ims-na1.adobelogin.com/ims/token/v3",
            json={"error": "invalid_client"},
            status=401,
        )

        with pytest.raises(Exception, match="access token"):
            gen._get_access_token()

    def test_get_headers_with_oauth(self):
        """Headers include OAuth bearer token."""
        gen = FireflyImageGenerator(
            client_id="test-id",
            client_secret="test-secret"
        )

        # Mock the token retrieval
        gen.access_token = "test-bearer-token"
        gen.token_expires_at = time.time() + 3600

        headers = gen._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-bearer-token"
        assert headers["Content-Type"] == "application/json"


class TestFireflyJobSubmission:
    """Test Firefly job submission."""

    @responses.activate
    def test_submit_generation_job_success(self):
        """Submit generation job successfully."""
        gen = FireflyImageGenerator(api_key="test-key")

        # Mock the submission response
        responses.add(
            responses.POST,
            "https://firefly-api.adobe.io/v3/images/generate-async",
            json={"jobId": "job-123-abc"},
            status=200,
        )

        job_id = gen._submit_generation_job(
            "test prompt",
            {"width": 1024, "height": 1024}
        )

        assert job_id == "job-123-abc"

    @responses.activate
    def test_submit_generation_job_missing_job_id(self):
        """Handle missing job ID in response."""
        gen = FireflyImageGenerator(api_key="test-key")

        responses.add(
            responses.POST,
            "https://firefly-api.adobe.io/v3/images/generate-async",
            json={"status": "accepted"},
            status=200,
        )

        with pytest.raises(Exception, match="No job ID"):
            gen._submit_generation_job(
                "test prompt",
                {"width": 1024, "height": 1024}
            )

    @responses.activate
    def test_submit_generation_job_api_error(self):
        """Handle API error during job submission."""
        gen = FireflyImageGenerator(api_key="test-key")

        responses.add(
            responses.POST,
            "https://firefly-api.adobe.io/v3/images/generate-async",
            json={"error": "Invalid prompt"},
            status=400,
        )

        with pytest.raises(Exception, match="job submission error"):
            gen._submit_generation_job(
                "test prompt",
                {"width": 1024, "height": 1024}
            )


class TestFireflyJobPolling:
    """Test Firefly job status polling."""

    @responses.activate
    def test_poll_job_completion_success(self):
        """Poll job until success."""
        gen = FireflyImageGenerator(api_key="test-key")

        # Mock status polling
        responses.add(
            responses.GET,
            "https://firefly-api.adobe.io/v3/status/job-123",
            json={"status": "PROCESSING"},
            status=200,
        )

        responses.add(
            responses.GET,
            "https://firefly-api.adobe.io/v3/status/job-123",
            json={
                "status": "SUCCEEDED",
                "result": {
                    "outputs": [
                        {
                            "image": {"url": "https://example.com/image.png"},
                            "seed": 42,
                        }
                    ]
                },
            },
            status=200,
        )

        image_url = gen._poll_job_completion("job-123")
        assert image_url == "https://example.com/image.png"

    @responses.activate
    def test_poll_job_completion_failed(self):
        """Handle job failure."""
        gen = FireflyImageGenerator(api_key="test-key")

        responses.add(
            responses.GET,
            "https://firefly-api.adobe.io/v3/status/job-123",
            json={
                "status": "FAILED",
                "error": {"message": "Invalid dimensions"},
            },
            status=200,
        )

        with pytest.raises(Exception, match="Generation failed"):
            gen._poll_job_completion("job-123")

    @responses.activate
    def test_poll_job_completion_timeout(self):
        """Timeout when job doesn't complete."""
        gen = FireflyImageGenerator(api_key="test-key")

        responses.add(
            responses.GET,
            "https://firefly-api.adobe.io/v3/status/job-123",
            json={"status": "PROCESSING"},
            status=200,
        )

        with pytest.raises(Exception, match="timed out"):
            gen._poll_job_completion("job-123", max_wait=1)


class TestFireflyImageGeneration:
    """Test image generation."""

    @responses.activate
    def test_generate_image_success(self):
        """Generate image successfully."""
        gen = FireflyImageGenerator(api_key="test-key")

        # Mock job submission
        responses.add(
            responses.POST,
            "https://firefly-api.adobe.io/v3/images/generate-async",
            json={"jobId": "job-123"},
            status=200,
        )

        # Mock job completion
        responses.add(
            responses.GET,
            "https://firefly-api.adobe.io/v3/status/job-123",
            json={
                "status": "SUCCEEDED",
                "result": {
                    "outputs": [
                        {
                            "image": {"url": "https://example.com/result.png"},
                            "seed": 42,
                        }
                    ]
                },
            },
            status=200,
        )

        result = gen.generate_image(
            product="Test Product",
            region="US",
            audience="Tech enthusiasts",
            message="Innovative solution",
        )

        assert result == "https://example.com/result.png"
        assert gen.images_generated == 1

    def test_generate_image_with_unsupported_size(self):
        """Handle unsupported image size."""
        gen = FireflyImageGenerator(api_key="test-key")

        with patch.object(gen, "_submit_generation_job") as mock_submit:
            with patch.object(gen, "_poll_job_completion") as mock_poll:
                mock_submit.return_value = "job-123"
                mock_poll.return_value = "https://example.com/image.png"

                gen.generate_image(
                    product="Product",
                    region="US",
                    audience="Audience",
                    message="Message",
                    size="9999x9999",  # Unsupported size
                )

                # Should default to 1024x1024
                call_args = mock_submit.call_args
                assert call_args[0][1]["width"] == 1024


class TestFireflyInheritance:
    """Test inheritance from base generator."""

    def test_firefly_inherits_from_base(self):
        """Firefly generator inherits from ImageGeneratorBase."""
        from app.generator import ImageGeneratorBase
        gen = FireflyImageGenerator(api_key="test-key")
        assert isinstance(gen, ImageGeneratorBase)

    def test_build_prompt_method(self):
        """Inherits working prompt builder."""
        gen = FireflyImageGenerator(api_key="test-key")
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

    def test_images_generated_counter(self):
        """Track images generated counter."""
        gen = FireflyImageGenerator(api_key="test-key")
        assert gen.images_generated == 0



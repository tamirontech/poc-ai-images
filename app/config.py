"""Application configuration management with type safety."""

from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized, type-safe application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    # API Keys
    openai_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    replicate_api_token: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("REPLICATE_API_TOKEN", "REPLICATE_API_KEY"),
    )
    google_api_key: Optional[str] = None

    # Adobe Firefly OAuth Credentials
    firefly_client_id: Optional[str] = None
    firefly_client_secret: Optional[str] = None
    # Legacy support: fallback to simple API key if OAuth not available
    firefly_api_key: Optional[str] = None

    # Image Generation
    default_image_provider: str = "dalle"
    image_generation_model: str = Field(
        default="dall-e-3",
        validation_alias=AliasChoices("IMAGE_GENERATION_MODEL", "DALLE_MODEL"),
    )
    huggingface_model: str = "stable-diffusion-3"
    replicate_model: str = "stable-diffusion-3"
    image_size: str = "1024x1024"
    max_retries: int = 3
    request_timeout_seconds: int = 60

    # Output
    app_env: str = "development"
    output_dir: str = "./outputs"
    log_dir: str = Field(
        default="./logs",
        validation_alias=AliasChoices("LOG_DIR", "LOGS_DIR"),
    )
    temp_dir: str = "./outputs/.tmp"

    # Processing
    max_text_length: int = 200
    aspect_ratios: list[str] = ["1:1", "9:16", "16:9"]

    # Compliance
    enable_compliance_checks: bool = True
    prohibited_words: list[str] = [
        "free",
        "guaranteed",
        "cure",
        "miracle",
        "100% effective",
        "clinically proven",
    ]

    # Logging
    log_level: str = "INFO"
    enable_json_logs: bool = True
    log_to_file: bool = True
    log_to_console: bool = True

    # Performance
    use_cache: bool = True
    cache_ttl_hours: int = 24
    concurrent_api_calls: int = 3

    def get_provider_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider.

        Args:
            provider: Provider name (dalle, huggingface, replicate, firefly, google)

        Returns:
            API key or None if not configured

        Raises:
            ValueError: If provider is unknown
        """
        provider_lower = provider.lower()

        if provider_lower == "dalle":
            return self.openai_api_key
        elif provider_lower == "huggingface":
            return self.huggingface_api_key
        elif provider_lower == "replicate":
            return self.replicate_api_token
        elif provider_lower == "firefly":
            # Firefly uses OAuth, not simple API key
            # Return client_id as token for validation
            return self.firefly_client_id or self.firefly_api_key
        elif provider_lower == "google":
            return self.google_api_key
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def validate_provider_config(self, provider: str) -> bool:
        """Validate that provider has required configuration.

        Args:
            provider: Provider name to validate

        Returns:
            True if provider is properly configured
        """
        if provider.lower() == "firefly":
            # Firefly requires either OAuth credentials or API key
            has_oauth = bool(self.firefly_client_id and self.firefly_client_secret)
            has_api_key = bool(self.firefly_api_key)
            return has_oauth or has_api_key

        api_key = self.get_provider_api_key(provider)
        return bool(api_key)


# Global settings instance
settings = Settings()

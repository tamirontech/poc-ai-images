"""Input validation and sanitization utilities for security."""

import re
from pathlib import Path
from typing import Optional


def sanitize_text_input(text: str, max_length: int = 200) -> str:
    """Sanitize user text input to prevent injection attacks.

    Args:
        text: User input text to sanitize
        max_length: Maximum allowed text length

    Returns:
        Sanitized text safe for image generation

    Raises:
        ValueError: If text is empty or invalid
    """
    if not text:
        raise ValueError("Text input cannot be empty")

    # Strip whitespace
    text = text.strip()

    if not text:
        raise ValueError("Text input cannot be whitespace only")

    # Limit length
    if len(text) > max_length:
        text = text[:max_length]

    # Remove control characters (ASCII 0-31 except newline/tab)
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t")

    # Remove multiple consecutive spaces
    text = re.sub(r" +", " ", text)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def validate_product_name(name: str, max_length: int = 100) -> str:
    """Validate and sanitize product name.

    Args:
        name: Product name to validate
        max_length: Maximum allowed length

    Returns:
        Validated product name

    Raises:
        ValueError: If product name is invalid
    """
    if not name:
        raise ValueError("Product name cannot be empty")

    name = name.strip()

    if not name:
        raise ValueError("Product name cannot be whitespace only")

    if len(name) > max_length:
        raise ValueError(f"Product name exceeds {max_length} characters")

    # Allow alphanumeric, spaces, hyphens, underscores
    if not re.match(r"^[a-zA-Z0-9 \-_]+$", name):
        raise ValueError(
            "Product name contains invalid characters. "
            "Use alphanumeric, spaces, hyphens, or underscores"
        )

    return name


def validate_file_path(file_path: str, allowed_base_dir: Optional[Path] = None) -> Path:
    """Validate file path to prevent directory traversal attacks.

    Args:
        file_path: File path to validate
        allowed_base_dir: Restrict access to this directory (default: current)

    Returns:
        Validated Path object

    Raises:
        ValueError: If path is invalid or outside allowed directory
    """
    path = Path(file_path).resolve()

    if allowed_base_dir:
        allowed_base = allowed_base_dir.resolve()
        try:
            path.relative_to(allowed_base)
        except ValueError:
            raise ValueError(
                f"File path {file_path} is outside allowed directory {allowed_base}"
            )

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return path


def sanitize_aspect_ratio(ratio: str) -> str:
    """Validate and standardize aspect ratio format.

    Args:
        ratio: Aspect ratio string (e.g., "1:1", "9:16")

    Returns:
        Validated aspect ratio string

    Raises:
        ValueError: If aspect ratio format is invalid
    """
    valid_ratios = {"1:1", "9:16", "16:9", "4:3", "3:2", "16:10"}

    if ratio not in valid_ratios:
        raise ValueError(
            f"Invalid aspect ratio: {ratio}. "
            f"Valid options: {', '.join(sorted(valid_ratios))}"
        )

    return ratio


def sanitize_region(region: str, max_length: int = 50) -> str:
    """Validate and sanitize region/market name.

    Args:
        region: Region name to validate
        max_length: Maximum allowed length

    Returns:
        Validated region name

    Raises:
        ValueError: If region is invalid
    """
    if not region:
        raise ValueError("Region cannot be empty")

    region = region.strip()

    if not region:
        raise ValueError("Region cannot be whitespace only")

    if len(region) > max_length:
        raise ValueError(f"Region exceeds {max_length} characters")

    # Allow alphanumeric, spaces, hyphens, forward slashes
    if not re.match(r"^[a-zA-Z0-9 \-/]+$", region):
        raise ValueError(
            "Region contains invalid characters. "
            "Use alphanumeric, spaces, hyphens, or slashes"
        )

    return region


class InputValidator:
    """Comprehensive input validation for campaign briefs."""

    @staticmethod
    def validate_campaign_brief_data(brief_data: dict) -> dict:
        """Validate all campaign brief input data.

        Args:
            brief_data: Dictionary with campaign metadata

        Returns:
            Validated and sanitized brief data

        Raises:
            ValueError: If any field fails validation
        """
        validated = {}

        # Validate products
        products = brief_data.get("products", [])
        if not isinstance(products, list):
            raise ValueError("Products must be a list")

        validated["products"] = [
            validate_product_name(p) for p in products
        ]

        if len(validated["products"]) < 2:
            raise ValueError("At least two different products are required")

        # Validate region
        validated["target_region"] = sanitize_region(
            brief_data.get("target_region", "")
        )

        # Validate audience
        validated["target_audience"] = sanitize_text_input(
            brief_data.get("target_audience", ""), max_length=500
        )

        # Validate campaign message
        validated["campaign_message"] = sanitize_text_input(
            brief_data.get("campaign_message", ""), max_length=200
        )

        # Optional: language
        language = brief_data.get("language", "en")
        if not isinstance(language, str) or len(language) > 10:
            raise ValueError("Invalid language code")
        validated["language"] = language

        # Optional: aspect ratios
        if "aspect_ratios" in brief_data:
            aspect_ratios = brief_data.get("aspect_ratios", [])
            if isinstance(aspect_ratios, list):
                validated["aspect_ratios"] = [
                    sanitize_aspect_ratio(ar) for ar in aspect_ratios
                ]
            else:
                raise ValueError("Aspect ratios must be a list")

        return validated

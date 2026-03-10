"""Campaign brief parser and validator."""

import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CampaignBrief(BaseModel):
    """Campaign brief schema."""

    model_config = ConfigDict(extra="forbid")

    products: List[str] = Field(
        ...,
        description="List of products (at least 2 different products required)",
    )
    target_region: str = Field(
        ...,
        description="Target market/region (e.g., 'Japan', 'US')",
    )
    target_audience: str = Field(
        ...,
        description="Target audience description",
    )
    campaign_message: str = Field(
        ...,
        description="Primary campaign message",
    )
    language: str = Field(
        default="en",
        description="Language code (e.g., 'en', 'ja', 'es')",
    )
    brand_colors: List[str] = Field(
        default_factory=list,
        description="Brand hex colors (e.g., ['#0066CC', '#FFFFFF'])",
    )
    aspect_ratios: List[str] = Field(
        default_factory=lambda: ["1:1", "9:16", "16:9"],
        description="Target aspect ratios for creatives",
    )
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context for image generation",
    )
    logo_path: Optional[str] = Field(
        default=None,
        description="Path to local logo file (PNG/JPG with transparency support)",
    )
    reference_image_path: Optional[str] = Field(
        default=None,
        description="Path to local reference image file for scene/style guidance",
    )
    logo_position: str = Field(
        default="bottom-right",
        description="Logo position: 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'",
    )
    logo_scale: float = Field(
        default=0.15,
        ge=0.1,
        le=0.5,
        description="Logo scale as fraction of image width (0.1-0.5)",
    )
    visual_guidelines: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional visual guideline metadata",
    )
    campaign_name: Optional[str] = Field(
        default=None,
        description="Optional campaign name for reporting/display",
    )

    @field_validator("products")
    @classmethod
    def validate_products(cls, v):
        """Validate product list is non-empty, normalized, and contains 2 distinct products."""
        if not v:
            raise ValueError("At least two different products are required")

        normalized = []
        seen = set()
        for product in v:
            cleaned = product.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                normalized.append(cleaned)

        if len(normalized) < 2:
            raise ValueError(
                "At least two different products are required "
                "(case-insensitive duplicates count as one)."
            )

        return normalized

    @field_validator("target_region")
    @classmethod
    def validate_region(cls, v):
        """Validate region is not empty."""
        if not v.strip():
            raise ValueError("Target region cannot be empty")
        return v.strip()

    @field_validator("aspect_ratios")
    @classmethod
    def validate_ratios(cls, v):
        """Validate aspect ratios format.

        Raises:
            ValueError: If aspect ratio is not in the valid set.
        """
        valid_ratios = {"1:1", "9:16", "16:9", "4:3", "3:2", "16:10"}
        required_minimum = ["1:1", "9:16", "16:9"]

        for ratio in v:
            if ratio not in valid_ratios:
                valid_str = ", ".join(sorted(valid_ratios))
                msg = f"Invalid aspect ratio: {ratio}. Valid: {valid_str}"
                raise ValueError(msg)

        # Always produce at least the three core social formats.
        if not v:
            return required_minimum

        normalized = []
        for ratio in v:
            if ratio not in normalized:
                normalized.append(ratio)

        for ratio in required_minimum:
            if ratio not in normalized:
                normalized.append(ratio)

        return normalized

    @field_validator("logo_path")
    @classmethod
    def validate_logo_path(cls, v):
        """Validate and resolve logo path to input_assets folder.

        If logo_path is provided, resolves it to input_assets/ folder.
        Accepts paths like: 'logo.png', './logo.png', 'input_assets/logo.png', etc.

        Raises:
            FileNotFoundError: If logo file doesn't exist in input_assets folder.
        """
        if not v:
            return v

        logo_path = Path(v)
        
        # Extract just the filename if full path provided
        filename = logo_path.name
        
        # Check if file exists in input_assets folder
        input_assets_path = Path("./input_assets") / filename
        if input_assets_path.exists():
            return str(input_assets_path)
        
        # Also check current provided path as fallback (for absolute paths or other locations)
        if logo_path.exists():
            return str(logo_path)
        
        # File not found in either location
        raise FileNotFoundError(
            f"Logo file not found: {filename} not in ./input_assets/ and "
            f"path {v} does not exist. Place logo in ./input_assets/ folder."
        )

    @field_validator("reference_image_path")
    @classmethod
    def validate_reference_image_path(cls, v):
        """Validate and resolve reference image path to input_assets folder."""
        if not v:
            return v

        ref_path = Path(v)
        filename = ref_path.name
        input_assets_path = Path("./input_assets") / filename
        if input_assets_path.exists():
            return str(input_assets_path)

        if ref_path.exists():
            return str(ref_path)

        raise FileNotFoundError(
            f"Reference image not found: {filename} not in ./input_assets/ and "
            f"path {v} does not exist. Place reference image in ./input_assets/ folder."
        )

    @field_validator("logo_position")
    @classmethod
    def validate_logo_position(cls, v):
        """Validate logo position is one of allowed values.

        Raises:
            ValueError: If position is not valid.
        """
        valid_positions = {"top-left", "top-right", "bottom-left", "bottom-right", "center"}
        if v not in valid_positions:
            valid_str = ", ".join(sorted(valid_positions))
            msg = f"Invalid logo position: {v}. Valid: {valid_str}"
            raise ValueError(msg)
        return v


class BriefParser:
    """Parser for campaign briefs in JSON/YAML format."""

    @staticmethod
    def parse_file(file_path: str) -> CampaignBrief:
        """Parse campaign brief from JSON or YAML file.

        Args:
            file_path: Path to JSON or YAML file

        Returns:
            CampaignBrief instance

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid or content is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Brief file not found: {file_path}")

        if path.suffix.lower() == ".json":
            return BriefParser.parse_json(file_path)
        elif path.suffix.lower() in [".yaml", ".yml"]:
            return BriefParser.parse_yaml(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    @staticmethod
    def parse_json(file_path: str) -> CampaignBrief:
        """Parse JSON brief file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return CampaignBrief(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in brief file: {e}")

    @staticmethod
    def parse_yaml(file_path: str) -> CampaignBrief:
        """Parse YAML brief file."""
        try:
            with open(file_path, "r") as f:
                data = yaml.safe_load(f)
            return CampaignBrief(**data)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in brief file: {e}")

    @staticmethod
    def parse_dict(data: Dict[str, Any]) -> CampaignBrief:
        """Parse campaign brief from dictionary."""
        return CampaignBrief(**data)

"""Tests for campaign brief parser and validator."""

import pytest
import yaml
from pydantic import ValidationError

from app.parsers import CampaignBrief, BriefParser


class TestCampaignBrief:
    """Test CampaignBrief Pydantic model."""

    def test_valid_campaign_brief(self, sample_campaign_brief):
        """Valid campaign brief should create successfully."""
        assert sample_campaign_brief.products == ["EcoSoap", "NaturalShampoo"]
        assert sample_campaign_brief.target_region == "Japan"
        assert sample_campaign_brief.language == "en"

    def test_default_language(self):
        """Default language should be 'en'."""
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
        )
        assert brief.language == "en"

    def test_default_aspect_ratios(self):
        """Default aspect ratios should be ['1:1', '9:16', '16:9']."""
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
        )
        assert brief.aspect_ratios == ["1:1", "9:16", "16:9"]

    def test_empty_products_raises_error(self):
        """Empty products list should raise ValidationError."""
        with pytest.raises(ValidationError):
            CampaignBrief(
                products=[],
                target_region="US",
                target_audience="Young adults",
                campaign_message="Test message",
            )

    def test_empty_region_raises_error(self):
        """Empty region should raise ValidationError."""
        with pytest.raises(ValidationError):
            CampaignBrief(
                products=["Product1", "Product2"],
                target_region="",
                target_audience="Young adults",
                campaign_message="Test message",
            )

    def test_invalid_aspect_ratio_raises_error(self):
        """Invalid aspect ratio should raise ValidationError."""
        with pytest.raises(ValidationError):
            CampaignBrief(
                products=["Product1", "Product2"],
                target_region="US",
                target_audience="Young adults",
                campaign_message="Test message",
                aspect_ratios=["99:99"],  # Invalid
            )

    def test_valid_aspect_ratios(self):
        """All valid aspect ratios should be accepted."""
        valid_ratios = ["1:1", "9:16", "16:9", "4:3", "3:2", "16:10"]
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
            aspect_ratios=valid_ratios,
        )
        assert brief.aspect_ratios == valid_ratios

    def test_products_stripped_of_whitespace(self):
        """Products should be stripped of leading/trailing whitespace."""
        brief = CampaignBrief(
            products=["  Product1  ", "  Product2  "],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
        )
        assert brief.products == ["Product1", "Product2"]

    def test_region_stripped_of_whitespace(self):
        """Region should be stripped of leading/trailing whitespace."""
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="  US  ",
            target_audience="Young adults",
            campaign_message="Test message",
        )
        assert brief.target_region == "US"

    def test_single_product_raises_error(self):
        """Single product should fail requirement for 2 different products."""
        with pytest.raises(ValidationError, match="At least two different products are required"):
            CampaignBrief(
                products=["Product1"],
                target_region="US",
                target_audience="Young adults",
                campaign_message="Test message",
            )

    def test_case_insensitive_duplicate_products_raise_error(self):
        """Products that normalize to one distinct value should fail validation."""
        with pytest.raises(ValidationError, match="At least two different products are required"):
            CampaignBrief(
                products=["Soap", " soap "],
                target_region="US",
                target_audience="Young adults",
                campaign_message="Test message",
            )


class TestBriefParser:
    """Test BriefParser file parsing."""

    def test_parse_json_file(self, brief_json_file):
        """Parse valid JSON campaign brief."""
        brief = BriefParser.parse_file(str(brief_json_file))
        assert isinstance(brief, CampaignBrief)
        assert brief.products == ["EcoSoap", "NaturalShampoo"]

    def test_parse_yaml_file(self, temp_dir, sample_campaign_brief):
        """Parse valid YAML campaign brief."""
        yaml_path = temp_dir / "campaign.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(sample_campaign_brief.model_dump(), f)

        brief = BriefParser.parse_file(str(yaml_path))
        assert isinstance(brief, CampaignBrief)
        assert brief.products == ["EcoSoap", "NaturalShampoo"]

    def test_parse_invalid_json_raises_error(self, invalid_brief_json_file):
        """Invalid JSON should raise ValidationError."""
        with pytest.raises(ValidationError):
            BriefParser.parse_file(str(invalid_brief_json_file))

    def test_parse_nonexistent_file_raises_error(self):
        """Nonexistent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            BriefParser.parse_file("/nonexistent/path/campaign.json")

    def test_parse_json_from_dict(self, sample_campaign_brief):
        """Parse campaign brief from dictionary."""
        brief_dict = sample_campaign_brief.model_dump()
        brief = BriefParser.parse_dict(brief_dict)
        assert isinstance(brief, CampaignBrief)
        assert brief.target_region == "Japan"

    def test_parse_invalid_dict_raises_error(self):
        """Invalid dictionary should raise ValidationError."""
        with pytest.raises(ValidationError):
            BriefParser.parse_dict(
                {
                    "products": ["Product1"],
                    "target_region": "US",
                    "target_audience": "Young adults",
                    "campaign_message": "Test message",
                }
            )


class TestBriefValidators:
    """Test individual validators in CampaignBrief."""

    def test_validate_products_removes_empty_strings(self):
        """Empty strings in products should be removed."""
        brief = CampaignBrief(
            products=["Product1", "", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
        )
        assert brief.products == ["Product1", "Product2"]

    def test_validate_aspect_ratio_format(self):
        """Aspect ratio must be in 'W:H' format."""
        valid = ["1:1", "9:16", "16:9"]
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
            aspect_ratios=valid,
        )
        assert brief.aspect_ratios == valid

    def test_empty_aspect_ratio_list_uses_defaults(self):
        """Empty aspect ratio list should use defaults."""
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
            aspect_ratios=[],
        )
        assert brief.aspect_ratios == ["1:1", "9:16", "16:9"]

    def test_aspect_ratio_list_always_includes_three_core_formats(self):
        """Provided list should be expanded to include 1:1, 9:16, and 16:9."""
        brief = CampaignBrief(
            products=["Product1", "Product2"],
            target_region="US",
            target_audience="Young adults",
            campaign_message="Test message",
            aspect_ratios=["4:3"],
        )
        assert brief.aspect_ratios == ["4:3", "1:1", "9:16", "16:9"]

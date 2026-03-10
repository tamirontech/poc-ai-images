"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import json

from app.parsers import CampaignBrief
from app.processor import ImageProcessor
from app.compliance import ComplianceChecker
from app.storage import AssetStorage
from app.logger import PipelineLogger


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_campaign_brief():
    """Create a valid campaign brief for testing."""
    return CampaignBrief(
        products=["EcoSoap", "NaturalShampoo"],
        target_region="Japan",
        target_audience="Eco-conscious consumers aged 25-45",
        campaign_message="Discover nature's cleanest beauty solutions",
        language="en",
        brand_colors=["#00AA00", "#FFFFFF"],
        aspect_ratios=["1:1", "9:16", "16:9"],
        additional_context="Focus on sustainability and natural ingredients",
    )


@pytest.fixture
def sample_image(temp_dir):
    """Create a sample PIL Image for testing."""
    img = Image.new("RGB", (1024, 1024), color=(73, 109, 137))
    img_path = temp_dir / "sample.jpg"
    img.save(img_path)
    return img_path


@pytest.fixture
def image_processor():
    """Create ImageProcessor instance."""
    return ImageProcessor()


@pytest.fixture
def compliance_checker():
    """Create ComplianceChecker instance."""
    return ComplianceChecker(
        brand_colors=["#00AA00", "#FFFFFF"],
        prohibited_words=["banned", "illegal"],
    )


@pytest.fixture
def asset_storage(temp_dir):
    """Create AssetStorage instance with temporary directory."""
    return AssetStorage(base_dir=str(temp_dir))


@pytest.fixture
def pipeline_logger(temp_dir):
    """Create PipelineLogger instance."""
    return PipelineLogger(log_dir=str(temp_dir))


@pytest.fixture
def brief_json_file(temp_dir, sample_campaign_brief):
    """Create a temporary JSON campaign brief file."""
    json_path = temp_dir / "campaign.json"
    with open(json_path, "w") as f:
        json.dump(sample_campaign_brief.model_dump(), f)
    return json_path


@pytest.fixture
def invalid_brief_json_file(temp_dir):
    """Create temporary JSON file with invalid data."""
    json_path = temp_dir / "invalid.json"
    with open(json_path, "w") as f:
        json.dump({"invalid": "data"}, f)
    return json_path

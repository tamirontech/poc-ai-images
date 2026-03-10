"""End-to-end test for asset pipeline with mock generator."""

import json
from pathlib import Path

from app.main import CreativeAutomationPipeline
from app.parsers import BriefParser


class DummyGenerator:
    def __init__(self, image_path: Path):
        self.image_path = str(image_path)

    def generate_image(self, *args, **kwargs):
        return self.image_path

    def download_image(self, image_url: str, output_path: str):
        from shutil import copy2
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        copy2(image_url, output_path)
        return output_path


def test_pipeline_generates_reports_and_assets_with_logo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    input_assets = tmp_path / "input_assets"
    input_assets.mkdir(parents=True, exist_ok=True)

    logo_path = input_assets / "sample_logo.png"
    from PIL import Image

    Image.new("RGBA", (120, 120), color=(45, 80, 22, 255)).save(logo_path)

    brief_data = {
        "products": ["EcoSoap", "NaturalShampoo"],
        "target_region": "US",
        "target_audience": "Eco-conscious consumers",
        "campaign_message": "Clean products for modern life",
        "aspect_ratios": ["1:1", "9:16", "16:9"],
        "logo_path": "sample_logo.png",
        "brand_colors": ["#2D5016", "#FFFFFF"],
    }

    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief_data), encoding="utf-8")

    brief = BriefParser.parse_file(str(brief_path))

    seed_image = tmp_path / "seed.png"
    Image.new("RGB", (1024, 1024), color=(120, 120, 120)).save(seed_image)
    monkeypatch.setattr(
        CreativeAutomationPipeline,
        "_create_generator",
        lambda self, provider: DummyGenerator(seed_image),
    )
    pipeline = CreativeAutomationPipeline(provider="dalle", output_dir=str(tmp_path / "outputs"))
    result = pipeline.process_campaign(brief)

    assert result["failed"] == 0

    json_report = Path(result["report_json"])
    html_report = Path(result["report_html"])

    assert json_report.exists()
    assert html_report.exists()

    products_root = tmp_path / "outputs" / "products"
    assert products_root.exists()

    generated_pngs = list(products_root.rglob("*.png"))
    # 2 products * 3 aspect ratios
    assert len(generated_pngs) == 6

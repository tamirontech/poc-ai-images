"""Tests for temporary file location configuration."""

from pathlib import Path

from app.main import CreativeAutomationPipeline


def test_pipeline_uses_output_tmp_for_downloads(tmp_path):
    out_dir = tmp_path / "outputs"
    pipeline = CreativeAutomationPipeline.__new__(CreativeAutomationPipeline)
    pipeline.output_dir = str(out_dir)

    tmp_download_dir = Path(pipeline.output_dir) / ".tmp"
    assert str(tmp_download_dir).endswith("outputs/.tmp")


def test_asset_manager_dirs_are_under_configured_paths(tmp_path, monkeypatch):
    out_dir = tmp_path / "outputs"
    input_dir = tmp_path / "input_assets"
    input_dir.mkdir(parents=True, exist_ok=True)

    class _StubGenerator:
        def generate_image(self, *args, **kwargs):
            return ""

        def download_image(self, image_url: str, output_path: str):
            return output_path

    monkeypatch.setattr(
        CreativeAutomationPipeline,
        "_create_generator",
        lambda self, provider: _StubGenerator(),
    )
    pipeline = CreativeAutomationPipeline(provider="dalle", output_dir=str(out_dir))

    assert pipeline.asset_manager.cache_dir == out_dir / "products"
    assert pipeline.asset_manager.input_dir == Path("./input_assets")

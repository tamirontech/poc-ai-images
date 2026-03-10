"""Tests for fallback behavior priority."""

from pathlib import Path

from app.asset_manager import AssetInputManager


def _create_png(path: Path):
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (512, 512), color=(200, 50, 50)).save(path, format="PNG")


def test_three_level_fallback_priority(tmp_path):
    input_dir = tmp_path / "input_assets"
    cache_dir = tmp_path / "outputs" / "products"

    _create_png(input_dir / "EcoSoap_input.png")
    _create_png(cache_dir / "EcoSoap" / "9-16" / "EcoSoap_9-16_cached.png")

    manager = AssetInputManager(input_dir=str(input_dir), cache_dir=str(cache_dir))

    # Cached ratio available -> cached wins.
    ratio_asset, ratio_source = manager.get_asset_with_fallback(
        "EcoSoap", "US", "msg", "9:16"
    )
    assert ratio_asset is not None
    assert ratio_source == "cached:ratio"

    # No cached ratio -> input fallback.
    input_asset, input_source = manager.get_asset_with_fallback(
        "EcoSoap", "US", "msg", "1:1"
    )
    assert input_asset is not None
    assert input_source == "input"

    # No cached + no input -> generation needed.
    none_asset, none_source = manager.get_asset_with_fallback(
        "NewProduct", "US", "msg", "16:9"
    )
    assert none_asset is None
    assert none_source is None

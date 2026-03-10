"""Unit tests for AssetInputManager."""

from pathlib import Path

from app.asset_manager import AssetInputManager


def _create_png(path: Path, size: tuple[int, int] = (1024, 1024)):
    from PIL import Image

    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(120, 140, 160)).save(path, format="PNG")


def test_fallback_prefers_cached_ratio(tmp_path):
    input_dir = tmp_path / "input_assets"
    cache_dir = tmp_path / "outputs" / "products"

    _create_png(input_dir / "EcoSoap_input.png")
    _create_png(cache_dir / "EcoSoap" / "1-1" / "EcoSoap_1-1_cached.png")

    manager = AssetInputManager(input_dir=str(input_dir), cache_dir=str(cache_dir))

    asset_path, source = manager.get_asset_with_fallback(
        "EcoSoap", "US", "message", "1:1"
    )

    assert asset_path is not None
    assert source == "cached:ratio"


def test_fallback_uses_input_when_no_cached_ratio(tmp_path):
    input_dir = tmp_path / "input_assets"
    cache_dir = tmp_path / "outputs" / "products"

    _create_png(input_dir / "EcoSoap_input.png")
    manager = AssetInputManager(input_dir=str(input_dir), cache_dir=str(cache_dir))

    asset_path, source = manager.get_asset_with_fallback(
        "EcoSoap", "US", "message", "9:16"
    )

    assert asset_path is not None
    assert source == "input"


def test_fallback_returns_none_when_no_assets(tmp_path):
    input_dir = tmp_path / "input_assets"
    cache_dir = tmp_path / "outputs" / "products"

    manager = AssetInputManager(input_dir=str(input_dir), cache_dir=str(cache_dir))

    asset_path, source = manager.get_asset_with_fallback(
        "NewProduct", "US", "message", "16:9"
    )

    assert asset_path is None
    assert source is None


def test_copy_input_to_cache_creates_output_file(tmp_path):
    input_dir = tmp_path / "input_assets"
    cache_dir = tmp_path / "outputs" / "products"

    input_logo = input_dir / "EcoSoap_input.png"
    _create_png(input_logo)

    manager = AssetInputManager(input_dir=str(input_dir), cache_dir=str(cache_dir))
    copied = manager.copy_input_to_cache(input_logo, "EcoSoap", "1:1")

    assert copied.exists()
    assert copied.parent.name == "1-1"

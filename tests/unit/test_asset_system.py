"""Tests for asset path resolution in campaign briefs."""


import pytest

from app.parsers import CampaignBrief


def _base_brief_data() -> dict:
    return {
        "products": ["EcoSoap", "NaturalShampoo"],
        "target_region": "US",
        "target_audience": "eco-conscious consumers",
        "campaign_message": "Save the planet",
    }


def test_logo_filename_resolves_from_input_assets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    input_assets = tmp_path / "input_assets"
    input_assets.mkdir()

    logo_path = input_assets / "test_logo.png"
    logo_path.write_bytes(b"fake")

    brief = CampaignBrief(**{**_base_brief_data(), "logo_path": "test_logo.png"})
    assert "input_assets/test_logo.png" in brief.logo_path


def test_logo_path_accepts_existing_explicit_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    input_assets = tmp_path / "input_assets"
    input_assets.mkdir()

    logo_path = input_assets / "test_logo.png"
    logo_path.write_bytes(b"fake")

    brief = CampaignBrief(
        **{**_base_brief_data(), "logo_path": str(logo_path)}
    )
    assert brief.logo_path.endswith("test_logo.png")


def test_missing_logo_raises_file_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "input_assets").mkdir()

    with pytest.raises(FileNotFoundError):
        CampaignBrief(**{**_base_brief_data(), "logo_path": "missing_logo.png"})


def test_logo_is_optional(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    brief = CampaignBrief(**_base_brief_data())
    assert brief.logo_path is None

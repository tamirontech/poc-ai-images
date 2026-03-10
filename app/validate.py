"""Unified validation CLI for local sanity checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.asset_manager import AssetInputManager
from app.parsers import BriefParser


REQUIRED_ASSET_MANAGER_METHODS = [
    "find_input_asset",
    "list_input_assets",
    "validate_input_asset",
    "get_input_asset_info",
]


def _result(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "ok": True,
        "errors": [],
        "warnings": [],
        "details": {},
    }


def validate_asset_manager(input_dir: str, strict: bool) -> dict[str, Any]:
    result = _result("asset-manager")

    try:
        manager = AssetInputManager(input_dir=input_dir, cache_dir="./outputs/products")
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(f"failed to initialize AssetInputManager: {exc}")
        return result

    missing_methods = [
        method for method in REQUIRED_ASSET_MANAGER_METHODS if not hasattr(manager, method)
    ]
    if missing_methods:
        result["ok"] = False
        result["errors"].append(f"missing expected methods: {', '.join(missing_methods)}")

    assets = manager.list_input_assets()
    invalid_assets = []
    for product, path in assets.items():
        is_valid, message = manager.validate_input_asset(path)
        if not is_valid:
            invalid_assets.append({"product": product, "path": str(path), "message": message})

    if invalid_assets:
        result["ok"] = False
        result["errors"].append(
            "invalid input assets found: "
            + "; ".join(f"{item['product']} ({item['message']})" for item in invalid_assets)
        )

    if not assets:
        warning = f"no input assets found in {Path(input_dir)}"
        if strict:
            result["ok"] = False
            result["errors"].append(warning)
        else:
            result["warnings"].append(warning)

    info = manager.get_input_asset_info()
    result["details"] = {
        "input_dir": str(manager.input_dir),
        "asset_count": len(assets),
        "assets": {product: str(path) for product, path in assets.items()},
        "input_asset_info": info,
    }
    return result


def validate_hf_example(brief_path: str, strict: bool) -> dict[str, Any]:
    result = _result("hf-example")

    try:
        brief = BriefParser.parse_file(brief_path)
    except Exception as exc:
        result["ok"] = False
        result["errors"].append(f"failed to parse brief {brief_path}: {exc}")
        return result

    logo_exists = False
    logo_size_kb = None
    if brief.logo_path:
        logo_file = Path(brief.logo_path)
        logo_exists = logo_file.exists()
        if logo_exists:
            logo_size_kb = round(logo_file.stat().st_size / 1024, 1)
        elif strict:
            result["ok"] = False
            result["errors"].append(f"logo path does not exist: {brief.logo_path}")
        else:
            result["warnings"].append(f"logo path does not exist: {brief.logo_path}")
    else:
        msg = "brief has no logo_path configured"
        if strict:
            result["ok"] = False
            result["errors"].append(msg)
        else:
            result["warnings"].append(msg)

    if not brief.additional_context:
        result["warnings"].append("brief has no additional_context")

    result["details"] = {
        "brief_path": brief_path,
        "products": brief.products,
        "target_region": brief.target_region,
        "target_audience": brief.target_audience,
        "campaign_message_preview": brief.campaign_message[:80],
        "brand_colors": brief.brand_colors,
        "aspect_ratios": brief.aspect_ratios,
        "logo_path": brief.logo_path,
        "logo_exists": logo_exists,
        "logo_size_kb": logo_size_kb,
    }
    return result


def run_all(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        validate_asset_manager(args.input_dir, args.strict),
        validate_hf_example(args.brief, args.strict),
    ]


def _print_human(results: list[dict[str, Any]], quiet: bool) -> None:
    for res in results:
        state = "PASS" if res["ok"] else "FAIL"
        print(f"[{state}] {res['name']}")
        if quiet:
            continue
        for err in res["errors"]:
            print(f"  error: {err}")
        for warn in res["warnings"]:
            print(f"  warning: {warn}")
        for key, value in res["details"].items():
            print(f"  {key}: {value}")
        print("")

    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    print(f"Summary: {passed}/{total} checks passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validation CLI for project sanity checks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--strict", action="store_true", help="Fail on warnings")
    common.add_argument("--json", action="store_true", help="Emit JSON output")
    common.add_argument("--quiet", action="store_true", help="Reduce text output")

    asset_parser = subparsers.add_parser(
        "asset-manager",
        parents=[common],
        help="Validate AssetInputManager wiring and local input assets",
    )
    asset_parser.add_argument(
        "--input-dir",
        default="./input_assets",
        help="Input assets directory (default: ./input_assets)",
    )

    hf_parser = subparsers.add_parser(
        "hf-example",
        parents=[common],
        help="Validate HuggingFace example brief parsing and logo references",
    )
    hf_parser.add_argument(
        "--brief",
        default="examples/huggingface_brief.json",
        help="Brief path (default: examples/huggingface_brief.json)",
    )

    all_parser = subparsers.add_parser(
        "all",
        parents=[common],
        help="Run all validation checks",
    )
    all_parser.add_argument(
        "--input-dir",
        default="./input_assets",
        help="Input assets directory (default: ./input_assets)",
    )
    all_parser.add_argument(
        "--brief",
        default="examples/huggingface_brief.json",
        help="Brief path (default: examples/huggingface_brief.json)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "asset-manager":
        results = [validate_asset_manager(args.input_dir, args.strict)]
    elif args.command == "hf-example":
        results = [validate_hf_example(args.brief, args.strict)]
    else:
        results = run_all(args)

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        _print_human(results, quiet=args.quiet)

    return 0 if all(res["ok"] for res in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

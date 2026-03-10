#!/usr/bin/env python3
"""Standalone wrapper for asset-manager validation."""

import argparse
import json

from app.validate import validate_asset_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AssetInputManager and input assets")
    parser.add_argument("--input-dir", default="./input_assets")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate_asset_manager(args.input_dir, args.strict)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        state = "PASS" if result["ok"] else "FAIL"
        print(f"[{state}] asset-manager")
        for err in result["errors"]:
            print(f"  error: {err}")
        for warn in result["warnings"]:
            print(f"  warning: {warn}")
        print(f"  input_dir: {result['details']['input_dir']}")
        print(f"  asset_count: {result['details']['asset_count']}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

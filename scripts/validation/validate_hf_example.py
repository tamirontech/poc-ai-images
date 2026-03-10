#!/usr/bin/env python3
"""Standalone wrapper for HuggingFace example validation."""

import argparse
import json

from app.validate import validate_hf_example


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate HuggingFace example brief")
    parser.add_argument("--brief", default="examples/huggingface_brief.json")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = validate_hf_example(args.brief, args.strict)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        state = "PASS" if result["ok"] else "FAIL"
        print(f"[{state}] hf-example")
        for err in result["errors"]:
            print(f"  error: {err}")
        for warn in result["warnings"]:
            print(f"  warning: {warn}")
        print(f"  brief_path: {result['details'].get('brief_path', args.brief)}")
        print(f"  products: {result['details'].get('products', [])}")
        print(f"  logo_exists: {result['details'].get('logo_exists')}")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

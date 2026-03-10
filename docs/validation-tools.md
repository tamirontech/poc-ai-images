# Validation Tools Guide

This repo has a unified validation CLI and two standalone wrappers:

- `python -m app.validate` (new unified CLI)
- `scripts/validation/validate_asset_manager.py`
- `scripts/validation/validate_hf_example.py`

These are quick sanity checks, not a replacement for full smoke tests + pytest.

## Unified CLI (`python -m app.validate`)

Subcommands:
- `asset-manager`
- `hf-example`
- `all`

Shared flags:
- `--strict` (treat warnings as failures)
- `--json` (machine-readable output)
- `--quiet` (reduced text output)

Examples:

```bash
python -m app.validate all --json
python -m app.validate asset-manager --input-dir ./input_assets --cache-dir ./outputs/products
python -m app.validate hf-example --brief examples/huggingface_brief.json --strict
```

## 1) `validate_asset_manager.py`

Purpose:
- Instantiates `AssetInputManager` with:
  - `input_dir=./input_assets`
  - `cache_dir=./outputs`
- Confirms key methods exist on the manager object.
- Prints current input asset system status from `get_input_asset_info()`.

What it validates well:
- Basic import + initialization works.
- The expected API surface is present.
- Local asset directories are readable in your current environment.

What it does not validate:
- End-to-end generation behavior.
- Error handling across different invalid inputs.
- Contract-level outputs/assertions (it prints status instead of enforcing test assertions).

How to run (wrapper):

```bash
python scripts/validation/validate_asset_manager.py
python scripts/validation/validate_asset_manager.py --strict --json
```

## 2) `validate_hf_example.py`

Purpose:
- Parses `examples/huggingface_brief.json` using `BriefParser`.
- Prints parsed fields (products, region, audience, message, colors, logo config, aspect ratios, context).
- Checks whether the configured logo file exists and reports file size if present.

What it validates well:
- The Hugging Face example brief can be parsed.
- Example brief structure matches parser expectations.
- Referenced logo path is present.

What it does not validate:
- Any external provider API call.
- Full image generation pipeline correctness.
- Deterministic pass/fail criteria beyond parser/runtime exceptions.

How to run (wrapper):

```bash
python scripts/validation/validate_hf_example.py
python scripts/validation/validate_hf_example.py --brief examples/huggingface_brief.json --json
```

## Related Existing CLI

The project already has a structured CLI in `app/main.py`:

- `python -m app.main run ...`
- `python -m app.main serve ...`

And a test wrapper:

- `./run_tests.sh --quick|--smoke|--full`

For pipeline behavior and regression confidence, `run_tests.sh` + `pytest` is stronger than the validation scripts.

## Design Review Outcome

Creating a holistic CLI was the right direction. It now gives you:
- one command surface for local and CI use
- explicit flags instead of hardcoded paths
- non-zero exit codes on failed validation

Keep using `run_tests.sh` + pytest for regression confidence, and use `app.validate` for fast preflight checks.

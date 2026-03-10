# Changelog

## Unreleased

### Added
- Brand color compliance check (`ComplianceChecker.check_brand_colors`): pixel grid sampling with Euclidean RGB distance to verify that generated images contain sufficient brand color coverage.
- Post-generation compliance checks wired into the pipeline: dimension validation, brand color verification, and text overlay presence run automatically after each image is saved.

### Changed
- `run_full_check` now accepts `image_path` and `brand_colors` parameters to invoke image-level checks.
- Adobe Firefly integration doc corrected (removed stale Python docstring delimiters).
- Testing quick reference rewritten with correct CLI commands (`python -m app.main run --brief …`).

### Removed
- 18 stale documentation files (historical changelogs, progress reports, duplicate QA artifacts, redundant guides).
- "Text overlay only in English" limitation — multi-language/RTL rendering was already implemented.

---

## Previous

- Reorganized tests into `tests/unit`, `tests/integration`, and `tests/e2e`.
- Added stable pytest discovery config in `pyproject.toml`.
- Moved root technical documentation into `docs/` by topic.
- Standardized CLI command shape with `run` and `serve` subcommands.

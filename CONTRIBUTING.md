# Contributing

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   `pip install -e .[dev]`

## Development

1. Run smoke or full tests:
   `./run_tests.sh --smoke`
   `./run_tests.sh --full`
2. Keep changes scoped to one concern per PR.
3. Update relevant docs under `docs/` when behavior changes.

## Pull Requests

1. Include a short summary, test evidence, and any known limitations.
2. Prefer small, reviewable PRs over large mixed changes.

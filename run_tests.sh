#!/bin/bash

set -euo pipefail

MODE="${1:---full}"
OUTPUT_ROOT="test_outputs"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TEST_PROVIDER="${TEST_PROVIDER:-dalle}"

if [[ -x "venv/bin/python" ]]; then
    PYTHON_BIN="venv/bin/python"
fi

usage() {
    cat <<EOF
Usage: ./run_tests.sh [--quick | --smoke | --full]

Modes:
  --quick  Run one CLI smoke test (JSON brief)
  --smoke  Run CLI smoke tests (JSON + YAML briefs)
  --full   Run smoke tests + pytest suite (default)

Env:
  TEST_PROVIDER   Provider for smoke runs (default: dalle)
EOF
}

check_prereqs() {
    if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
        echo "Error: ${PYTHON_BIN} is required."
        exit 1
    fi
}

run_smoke_case() {
    local brief="$1"
    local out_dir="$2"

    echo "Running smoke: ${brief}"
    rm -rf "${out_dir}"

    "${PYTHON_BIN}" -m app.main \
        run \
        --brief "${brief}" \
        --provider "${TEST_PROVIDER}" \
        --output "${out_dir}"

    if ! find "${out_dir}" -maxdepth 1 -name 'report_*.json' | grep -q .; then
        echo "Error: smoke test did not produce report_*.json in ${out_dir}"
        exit 1
    fi
}

run_smoke() {
    mkdir -p "${OUTPUT_ROOT}"
    run_smoke_case "test_inputs/campaign_brief.json" "${OUTPUT_ROOT}/smoke_json"
    run_smoke_case "test_inputs/campaign_brief_enterprise.yaml" "${OUTPUT_ROOT}/smoke_yaml"
}

run_quick() {
    mkdir -p "${OUTPUT_ROOT}"
    run_smoke_case "test_inputs/campaign_brief.json" "${OUTPUT_ROOT}/smoke_json"
}

run_pytest() {
    echo "Running pytest suite..."
    "${PYTHON_BIN}" -m pytest -q
}

check_prereqs

case "${MODE}" in
    --quick)
        run_quick
        ;;
    --smoke)
        run_smoke
        ;;
    --full)
        run_smoke
        run_pytest
        ;;
    *)
        usage
        exit 1
        ;;
esac

echo "Test run completed: ${MODE}"

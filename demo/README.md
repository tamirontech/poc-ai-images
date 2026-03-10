# 2-3 Minute Demo Script

Use this script to record the required interview demo. Keep total runtime between 2 and 3 minutes.

## 0) Prep (before recording)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 1) Show repository and docs (20-30s)

- Open `README.md` and point out:
  - How to run
  - Example input/output
  - Key design decisions
  - Assumptions/limitations
- Open `DELIVERABLES_CHECKLIST.md`.

## 2) Run CLI flow locally (60-90s)

```bash
source venv/bin/activate
python -m app.main run --brief examples/sample_brief.json --mock
```

Show terminal output summary, then show generated files:

```bash
find outputs/products -maxdepth 3 -type d | sort
ls -la outputs/products/EcoSoap/1-1
```

## 3) Show web mode (30-45s)

```bash
python -m app.main serve --port 8000
```

- Open `http://localhost:8000`
- Trigger one generation run (mock is fine)
- Show result cards/images.

## 4) Close with constraints and tradeoffs (15-20s)

- Mention this is a PoC.
- Mention provider abstraction, asset reuse, and organized output structure.
- Mention optional checks (compliance/logging/reporting) are implemented.

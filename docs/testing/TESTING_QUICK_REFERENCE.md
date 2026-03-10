# Testing Quick Reference

## Run the pipeline

```bash
# No API key needed — uses DALL-E mock provider
python -m app.main run --brief examples/sample_brief.json --provider dalle

# With a real provider (requires API key in .env)
python -m app.main run --brief examples/sample_brief.json --provider dalle
python -m app.main run --brief examples/sample_brief.json --provider huggingface
python -m app.main run --brief examples/sample_brief.json --provider replicate
python -m app.main run --brief examples/sample_brief.json --provider firefly

# Custom output directory
python -m app.main run --brief examples/sample_brief.json --output ./my_outputs

# Start web server
python -m app.main serve --port 8000
```

## Run unit tests

```bash
pytest tests/ -v
pytest tests/ --cov=app
```

## Validation tools

```bash
# Check asset manager + brief wiring
python -m app.validate all

# Check just input assets
python -m app.validate asset-manager --input-dir ./input_assets

# Check a brief file
python -m app.validate hf-example --brief examples/huggingface_brief.json

# Strict mode (warnings become failures) + JSON output
python -m app.validate all --strict --json
```

## Verify outputs

```bash
# Check generated files
find outputs/products -name "*.png" | sort

# Check image dimensions (requires PIL)
python -c "
from PIL import Image
import os
for root, dirs, files in os.walk('outputs/products'):
    for f in files:
        if f.endswith('.png'):
            path = os.path.join(root, f)
            img = Image.open(path)
            print(f'{path}: {img.width}x{img.height}')
"

# View report
python -m json.tool outputs/report_*.json | head -60
```

## Expected output structure

```
outputs/
├── products/
│   ├── EcoSoap/
│   │   ├── 1-1/        # 1024x1024
│   │   ├── 9-16/       # 576x1024
│   │   └── 16-9/       # 1024x576
│   └── NaturalShampoo/
│       ├── 1-1/
│       ├── 9-16/
│       └── 16-9/
├── report_YYYYMMDD_HHMMSS.json
└── report_YYYYMMDD_HHMMSS.html
```

## What the pipeline always does

- Text overlay (campaign message) is applied to every image automatically — no flag needed
- Compliance checks run automatically (prohibited words + brand color coverage + dimensions)
- Input assets from `input_assets/` are auto-detected by product name — no flag needed
- Logs go to `logs/pipeline.log`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: python` | Use `python3` or activate venv: `source venv/bin/activate` |
| `ModuleNotFoundError: No module named 'app'` | Run from project root with `python -m app.main` |
| `OPENAI_API_KEY not set` | Use `--provider dalle` for testing (no key needed) |
| `Address already in use` | Use `--port 9000` or kill existing process: `lsof -i :8000` |
| Input asset not picked up | Name file `{ProductName}.png` in `input_assets/` — spelling must match brief |

# Creative Automation Pipeline for Localized Social Campaigns

AI-powered pipeline that converts structured campaign briefs into localized, multi-format social ad creatives at scale.

The system demonstrates how marketing teams can automate creative production while keeping brand structure, compliance checkpoints, and output organization predictable.

**Status:** MVP Complete | Demo Ready

---

## Documentation

- Full documentation index: [docs/README.md](./docs/README.md)
- Contribution guide: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Changelog: [CHANGELOG.md](./CHANGELOG.md)

---

## Executive Summary

Organizations running localized campaigns across regions and social platforms face a recurring operations problem:

- Creative asset production is slow and manual
- Ad formats vary by placement and platform
- Messaging changes across products, audiences, and regions
- Brand and compliance review adds friction
- Production cost scales with campaign volume

This project explores a pipeline-oriented architecture where a structured campaign brief produces standardized campaign outputs automatically.

The system transforms a campaign brief into multiple creatives through a modular workflow that includes:

- validation
- prompt construction
- asset generation
- image processing
- compliance checks
- deterministic storage
- reporting

---

## What The System Does

For each campaign brief, the pipeline can:

1. Parse and validate JSON or YAML input
2. Generate images for each product and aspect ratio
3. Resize and process assets for supported output formats
4. Apply message overlays
5. Add logo branding
6. Run compliance-oriented checks
7. Save outputs in a deterministic directory structure
8. Produce logs and campaign reports

The current implementation supports these aspect ratios:

- `1:1`
- `9:16`
- `16:9`

Generation time depends on provider speed, rate limits, and the number of requested assets.

---

## Design Principles

### Separation of Concerns

Pipeline stages are isolated into focused modules:

- brief parsing
- generation
- processing
- compliance
- storage
- reporting

### Provider Portability

Image generation vendors are abstracted behind a shared interface so the pipeline can switch between:

- DALL-E
- Hugging Face
- Replicate
- Firefly
- Google

### Deterministic Outputs

Generated assets are organized by product and aspect ratio so downstream automation can rely on a stable file layout.

### Cost-Aware Generation

The pipeline checks reusable local assets before invoking paid generation APIs to reduce cost and latency.

### Single Pipeline, Multiple Interfaces

The CLI and web UI run on the same orchestration logic to keep behavior consistent across interfaces.

### Production-Oriented Boundaries

This repository is still an MVP, but the architecture leaves clear extension points for:

- job queues
- cloud storage
- approval workflows
- analytics pipelines

---

## System Architecture

```text
Campaign Brief
(JSON / YAML)
      |
      v
Parser & Validator
      |
      v
Creative Pipeline
|- Cache Lookup
|- Prompt Construction
|- Image Generation
|- Image Processing
|- Text Overlay
|- Logo Placement
|- Compliance Checks
`- Asset Storage
      |
      v
Output Artifacts
|- Platform Creatives
`- Generation Report
```

Each stage produces artifacts and metadata that feed the final campaign report.

---

## Core Components

| Module | Responsibility |
|-------|----------------|
| `parsers.py` | Campaign brief parsing and validation |
| `generator.py` | Provider abstraction and image generation |
| `processor.py` | Resizing, text overlays, logo placement |
| `compliance.py` | Messaging and output validation checks |
| `storage.py` | File organization and reusable asset handling |
| `logger.py` | Structured logging and report generation |
| `main.py` | CLI entry point and FastAPI web server |

---

## Project Structure

```text
poc-ai-images/
├── app/
│   ├── main.py
│   ├── parsers.py
│   ├── generator.py
│   ├── processor.py
│   ├── compliance.py
│   ├── storage.py
│   └── logger.py
├── templates/
├── examples/
├── input_assets/
├── outputs/
├── logs/
├── tests/
├── pyproject.toml
├── README.md
└── .env.example
```

---

## Quick Start

### Prerequisites

- Python `3.10-3.13`
- `pip`
- At least one provider credential if you want to generate new images

Use Python `3.13` on macOS for the smoothest setup. Python `3.14` is currently not supported by this dependency set.

### 1. Create a virtual environment

This isolates the project dependencies from your system Python and avoids Homebrew-managed environment issues on macOS.

```bash
python3.13 -m venv venv
source venv/bin/activate
python --version
```

### 2. Upgrade pip

This reduces dependency installation issues, especially for binary wheels.

```bash
pip install --upgrade pip
```

### 3. Install dependencies

Install the project and development dependencies needed to run the CLI, web UI, and tests.

```bash
pip install -r requirements.txt
```

### 4. Configure provider credentials

This step is required before running any provider-backed generation command. The current codebase does not expose a separate no-key mock provider in the CLI.

```bash
cp .env.example .env
```

Edit `.env` and set the provider credential you actually plan to use:

- `OPENAI_API_KEY` for `dalle`
- `HUGGINGFACE_API_KEY` for `huggingface`
- `REPLICATE_API_TOKEN` for `replicate`
- `FIREFLY_API_KEY` or Firefly OAuth credentials for `firefly`
- `GOOGLE_API_KEY` for `google`

### 5. Run the CLI

Generate assets from a campaign brief:

```bash
python -m app.main run --brief examples/sample_brief.json --provider dalle
```

Other valid providers:

```bash
python -m app.main run --brief examples/sample_brief.json --provider huggingface
python -m app.main run --brief examples/sample_brief.json --provider replicate
python -m app.main run --brief examples/sample_brief.json --provider firefly
python -m app.main run --brief examples/sample_brief.json --provider google
```

Outputs are written under `outputs/`.

### 6. Run the web UI

Start the FastAPI interface:

```bash
python -m app.main serve --port 8000
```

You can also start the web UI with a specific provider:

```bash
python -m app.main serve --port 8000 --provider replicate
```

Then open `http://localhost:8000`.

### Example output structure

```text
outputs/
├── products/
│   ├── EcoSoap/
│   │   ├── 1-1/
│   │   ├── 9-16/
│   │   └── 16-9/
│   └── NaturalShampoo/
│       ├── 1-1/
│       ├── 9-16/
│       └── 16-9/
├── report_YYYYMMDD_HHMMSS.json
└── report_YYYYMMDD_HHMMSS.html
```

---

---

## 📋 Campaign Brief Format

Campaign briefs define the creative direction. Two formats are supported:

### JSON Format

```json
{
  "products": ["ProductA", "ProductB"],
  "target_region": "Japan",
  "target_audience": "Young professionals, eco-conscious",
  "campaign_message": "Sustainable self-care for a better tomorrow",
  "language": "en",
  "brand_colors": ["#2D5016", "#FFFFFF"],
  "aspect_ratios": ["1:1", "9:16", "16:9"],
  "additional_context": "Modern, minimalist design with natural elements"
}
```

### YAML Format

```yaml
products:
  - ProductA
  - ProductB

target_region: Japan
target_audience: Young professionals, eco-conscious
campaign_message: Sustainable self-care for a better tomorrow

language: en
brand_colors:
  - "#2D5016"
  - "#FFFFFF"

aspect_ratios:
  - "1:1"
  - "9:16"
  - "16:9"

additional_context: Modern, minimalist design with natural elements
```

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `products` | Array | Product names (2+ distinct required, case-insensitive) | `["EcoSoap", "ShampooBar"]` |
| `target_region` | String | Geographic/market region | `"Japan"`, `"US West"` |
| `target_audience` | String | Audience segment description | `"Young professionals, eco-conscious"` |
| `campaign_message` | String | Primary message/tagline | `"Sustainable self-care"` |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | String | `"en"` | Language code: `en`, `es`, `ja`, `de`, `fr` |
| `brand_colors` | Array | `[]` | Hex color codes for brand compliance |
| `aspect_ratios` | Array | `["1:1","9:16","16:9"]` | Target formats for creatives |
| `additional_context` | String | `""` | Style/mood/constraints for generation |
| `logo_path` | String | `null` | Local path to logo file (PNG/JPG with transparency) |
| `logo_position` | String | `"bottom-right"` | Logo position: `top-left`, `top-right`, `bottom-left`, `bottom-right`, `center` |
| `logo_scale` | Number | `0.15` | Logo size as fraction of image width (0.1-0.5) |

**Validation note:** `products` must contain at least **two different** values after trimming and case-insensitive normalization. Example: `"Soap"` and `" soap "` count as one.

---

## 🎨 Logo Configuration

Add branding to all generated images with your company logo.

### Logo Requirements

- **Formats:** PNG (with transparency) or JPG
- **Transparency:** PNG with alpha channel recommended for clean overlay
- **Size:** Any size; will be automatically resized
- **Placement:** Configurable corners or center
- **Scale:** 10-50% of image width (to avoid overwhelming content)

### Logo Configuration Examples

#### JSON Format

```json
{
  "products": ["ProductA", "ProductB"],
  "target_region": "US",
  "target_audience": "Young professionals",
  "campaign_message": "Premium quality, eco-friendly",
  "language": "en",
  "brand_colors": ["#2D5016", "#FFFFFF"],
  "logo_path": "./input_assets/logo.png",
  "logo_position": "bottom-right",
  "logo_scale": 0.15,
  "aspect_ratios": ["1:1", "9:16", "16:9"]
}
```

#### YAML Format

```yaml
products:
  - ProductA
  - ProductB

target_region: US
target_audience: Young professionals
campaign_message: Premium quality, eco-friendly

language: en
brand_colors:
  - "#2D5016"
  - "#FFFFFF"

logo_path: ./input_assets/logo.png
logo_position: bottom-right
logo_scale: 0.15

aspect_ratios:
  - "1:1"
  - "9:16"
  - "16:9"
```

#### Position Options

All generated images will have the logo placed according to your preference:

| Position | Best For |
|----------|----------|
| `bottom-right` | Default; doesn't interfere with product focus |
| `bottom-left` | Alternative corner placement |
| `top-right` | Prominent branding (risks covering content) |
| `top-left` | Alternative corner placement |
| `center` | Maximum logo visibility (use with subtle designs) |

#### Scale Guidelines

- **0.10 (10%):** Minimal, subtle branding
- **0.15 (15%):** Default, balanced visibility
- **0.20 (20%):** More prominent without overwhelming
- **0.30+ (30%+):** Bold branding; use with simple backgrounds

### Logo Usage Tips

1. **No venv friction:** Logo files can be anywhere, just provide the full or relative path
2. **Transparency matters:** PNG with alpha channel renders cleanly on any background
3. **File types:** Both PNG and JPG supported; automatic format detection
4. **Batch campaigns:** Different products can use different logos (future feature: per-product logos in array)
5. **Testing:** Use test generator to test logo placement without API calls:
   ```bash
   source venv/bin/activate
   python -m app.main run --brief examples/logo_brief.json --provider dalle
   ```

## 🏗️ Architecture & Design Decisions

### Component Overview

```
Campaign Brief (JSON/YAML)
        ↓
    Parser & Validator
        ↓
    ┌─────────────────────────────┐
    │  For each Product           │
    │  For each Aspect Ratio      │
    │    ├─ Check Cache           │
    │    ├─ Generate (DALL-E)     │
    │    ├─ Process & Resize      │
    │    ├─ Overlay Text          │
    │    ├─ Add Logo              │
    │    ├─ Compliance Checks     │
    │    └─ Save & Log            │
    └─────────────────────────────┘
        ↓
    Organized Outputs
    + Report
```

### Key Modules

#### `parsers.py` – Campaign Brief Validation
- Pydantic-based schema validation
- Supports JSON and YAML parsing
- Clear error messages for invalid inputs
- **Design choice:** Pydantic for type safety and auto-documentation

#### `generator.py` – Image Generation
- OpenAI DALL-E 3 API wrapper
- Hugging Face Inference API integration
- Replicate API integration
- Firefly and Google provider integrations
- Error handling and retry logic
- **Design choice:** Multiple providers for flexibility and provider portability

#### `processor.py` – Image Processing
- Pillow (PIL) for resizing, cropping, text overlay, and logo overlay
- Intelligent aspect ratio handling (center crop, preserve content)
- Text wrapping and drop-shadow for readability
- Logo placement with configurable position and scale
- PNG transparency support for clean logo compositing
- Multi-language support via prompt hints
- **Design choice:** Pillow avoids external service dependencies; sufficient for PoC

#### `storage.py` – Asset Management
- Local filesystem organization: `product/aspect-ratio/`
- Simple hashing-based cache lookup
- Scalable to cloud storage (S3, Azure Blob) later
- **Design choice:** Local storage for simplicity; extensible design for cloud

#### `compliance.py` – Compliance & Safety
- **Brand messaging**: Validate against prohibited words (customizable)
- **Content checks**: Image dimension validation for expected aspect ratios
- **Legal flagging**: Simple keyword matching (extensible to ML models)
- **Design choice:** Lightweight heuristics for MVP; production would use ML-based content moderation

#### `logger.py` – Observability
- Structured logging to file + console
- JSON report generation with generation metrics
- Cost estimation (DALL-E usage tracking)
- **Design choice:** Simple file-based logging; scales to centralized logging (ELK, DataDog) later

#### `main.py` – Orchestration
- CLI: batch processing of campaign briefs
- FastAPI web server: interactive UI + REST API
- Unified pipeline logic for both entry points
- **Design choice:** Both CLI and web for flexibility; share core pipeline logic

---

## 🔄 Generation Workflow

### Step 1: Parse & Validate
- Load campaign brief (JSON/YAML)
- Validate required fields and data types
- Fail fast with clear error messages

### Step 2: Compliance Pre-Check
- Check campaign message for prohibited words
- Flag any compliance issues before expensive DALL-E call

### Step 3: Cache Check
- For each product × aspect ratio combination:
  - Look for similar asset in local cache
  - If found, reuse and skip generation (cost savings)

### Step 4: Image Generation (DALL-E)
- Build optimized prompt from brief + product context
- Call DALL-E 3 API with size constraints
- Handle rate limits and timeouts gracefully

### Step 5: Download & Process
- Download image from DALL-E URL
- Resize to target aspect ratio (smart cropping)
- Overlay campaign message with drop shadow

### Step 6: Validation & Compliance
- Verify output dimensions match aspect ratio
- Check text overlay presence
- Validate against brand guidelines

### Step 7: Organization & Logging
- Save to `outputs/products/{product}/{aspect_ratio}/`
- Log generation metrics and compliance results
- Update report with costs and status

---

## 📊 Output & Reporting

### Generated Files Structure

```
outputs/
├── ProductA/
│   ├── 1-1/              # Square format (Instagram)
│   │   ├── ProductA_1-1_1709544000.png
│   │   └── ProductA_1-1_1709544010.png
│   ├── 9-16/             # Stories (Instagram, TikTok)
│   │   └── ProductA_9-16_1709544015.png
│   └── 16-9/             # Landscape (LinkedIn, YouTube)
│       └── ProductA_16-9_1709544020.png
├── ProductB/
│   ├── 1-1/
│   ├── 9-16/
│   └── 16-9/
└── report_20260304_120000.json
```

### Report Structure

```json
{
  "timestamp": "2026-03-04T12:00:00",
  "status": "completed",
  "duration_seconds": 45.2,
  "products": {
    "ProductA": [
      {
        "aspect_ratio": "1:1",
        "status": "success",
        "file_path": "outputs/ProductA/1-1/ProductA_1-1_1709544000.png",
        "compliance_notes": [],
        "cached": false,
        "timestamp": "2026-03-04T12:00:10"
      }
    ]
  },
  "generation_stats": {
    "total_requested": 6,
    "generated": 4,
    "cached": 2,
    "failed": 0,
    "cost_estimate_usd": 0.24
  },
  "compliance_summary": {
    "total_checks": 6,
    "passed": 6,
    "warnings": []
  }
}
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=sk-...

# Application
APP_ENV=development
LOG_LEVEL=INFO
OUTPUT_DIR=./outputs
LOGS_DIR=./logs

# DALL-E
DALLE_MODEL=dall-e-3
IMAGE_SIZE=1024x1024

# Compliance
BRAND_COLORS=#0066CC,#FFFFFF
PROHIBITED_WORDS=free,guaranteed,cure,miracle
```

### Python Configuration

- Minimum Python version: **3.10**
- Dependencies: See `pyproject.toml`
- Virtual environment recommended

---

## 🧪 Testing

### Test with a configured provider

```bash
# Ensure venv is activated
source venv/bin/activate

# Example using Replicate
python -m app.main run --brief examples/sample_brief.json --provider replicate
```

This verifies the full pipeline with a real provider configuration, including generation, processing, logging, and output layout.

### Unit Tests

```bash
# Activate venv first
source venv/bin/activate

# Run test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=app
```

---

## 🎨 Aspect Ratio Support

The pipeline automatically generates assets for multiple social platforms:

| Ratio | Dimensions | Platforms | Use Case |
|-------|-----------|-----------|----------|
| **1:1** | 1024×1024 | Instagram Feed, TikTok, Pinterest | Product shots, square compositions |
| **9:16** | 576×1024 | Instagram Stories, TikTok, Facebook Stories | Mobile-first, full-screen vertical |
| **16:9** | 1024×576 | LinkedIn, YouTube, Facebook Feed | Desktop, landscape compositions |

Custom ratios can be added by extending `ImageProcessor.TARGET_SIZES`.

---

## 🚨 Compliance & Safety

### Brand Messaging Checks
- Validates campaign message against prohibited word lists
- Examples: "free", "guaranteed", "miracle", "clinically proven"
- Warnings logged but don't block generation (for review)

### Content Compliance
- Dimension validation (ensures aspect ratio correctness)
- Text overlay presence verification
- Brand color verification via pixel grid sampling (Euclidean RGB distance)
- Extensible to image-based content moderation (future)

### Legal Considerations
- This PoC assumes you own usage rights to generated images (per OpenAI ToS)
- Review brand and regulatory requirements for your industry
- Legal content scanning is simplified; production systems should use dedicated APIs

---

## 🎨 Image Generation Providers

The pipeline supports multiple image generation services. Choose based on your needs:

### DALL-E 3 (Default)

**Quality:** ⭐⭐⭐⭐⭐ (Highest)  
**Cost:** $0.03 per image  
**Speed:** 10-20 seconds per image  
**Availability:** Production-ready, backed by OpenAI

**Setup:**

```bash
# 1. Get API key from https://platform.openai.com/api-keys
# 2. Edit .env
OPENAI_API_KEY=sk-...

# 3. Run (uses DALL-E by default)
python -m app.main run --brief examples/sample_brief.json
```

**Pros:**
- Highest quality images
- Best for production use
- Mature, stable API
- Excellent prompt understanding

**Cons:**
- Paid service (~$0.03/image)
- Requires OpenAI account
- API key needed for authentication

---

### Hugging Face Inference API

**Quality:** ⭐⭐⭐⭐ (Excellent)  
**Cost:** Free tier available, Pro $9/month  
**Speed:** 5-15 seconds per image  
**Availability:** Community-driven, open-source models

**Setup:**

```bash
# 1. Get token from https://huggingface.co/settings/tokens
# 2. Edit .env
HUGGINGFACE_API_KEY=hf_...
HUGGINGFACE_MODEL=stable-diffusion-3  # or flux-dev, flux-schnell

# 3. Run with provider flag
python -m app.main run --brief examples/sample_brief.json --provider huggingface
```

**Available Models:**
- `stable-diffusion-3` - Default, good balance of quality/speed
- `flux-dev` - Cutting-edge, higher quality
- `flux-schnell` - Fast, good for quick iterations

**Pros:**
- Free tier available
- Open-source models
- No usage limits on free tier
- Great for development/testing

**Cons:**
- Free tier has rate limits
- Quality slightly lower than DALL-E
- Community-dependent

---

### Replicate

**Quality:** ⭐⭐⭐⭐ (Excellent)  
**Cost:** Free tier + pay-as-you-go ($0.005-0.06/image)  
**Speed:** 10-30 seconds per image  
**Availability:** Reliable API, multiple model providers

**Setup:**

```bash
# 1. Get API key from https://replicate.com/signin
# 2. Edit .env
REPLICATE_API_KEY=r8_...
REPLICATE_MODEL=stable-diffusion-3  # or flux-dev, flux-schnell

# 3. Run with provider flag
python -m app.main run --brief examples/sample_brief.json --provider replicate
```

**Available Models:**
- `stable-diffusion-3` - Default
- `flux-dev` - Advanced
- `flux-schnell` - Fast

**Pros:**
- Simple API
- Multiple model options
- Pay-as-you-go pricing
- Good uptime

**Cons:**
- Paid service after free tier
- Slightly slower than direct API calls
- Rate limits on free tier

---

### Adobe Firefly

**Quality:** ⭐⭐⭐⭐⭐ (State-of-the-art)  
**Cost:** Variable by plan (free credits available)  
**Speed:** 20-40 seconds per image  
**Availability:** Production-ready, backed by Adobe

**Setup:**

```bash
# 1. Get API key from https://developer.adobe.com/console
# 2. Edit .env
FIREFLY_API_KEY=your-adobe-api-key

# 3. Run with provider flag
python -m app.main run --brief examples/sample_brief.json --provider firefly
```

**Features:**
- Text-to-image generation
- Photo and art content classes
- Multiple resolution options
- Async job processing with automatic polling

**Pros:**
- Cutting-edge generative AI
- Adobe Creative Cloud integration potential
- Comprehensive API documentation
- Content categorization (photo/art)
- Free tier available

**Cons:**
- Newer service
- Requires Adobe account
- Async processing (job polling)
- Lower availability compared to DALL-E

**Learn More:**
- 📖 [Firefly Integration Guide](./docs/providers/FIREFLY_INTEGRATION.md)
- 🔗 [Official Firefly API Docs](https://developer.adobe.com/firefly-services/)

---

### DALL-E Provider

**Quality:** ⭐⭐ (Placeholder)  
**Cost:** Free  
**Speed:** <1 second per image  
**Availability:** Always available

**Setup:**

```bash
# No setup needed - use --provider dalle flag
python -m app.main run --brief examples/sample_brief.json --provider dalle
```

**Pros:**
- No API key needed
- Instant generation
- Perfect for testing/demo
- No costs

**Cons:**
- Placeholder images only (not real creatives)
- Not suitable for production

---

## 📊 Provider Comparison

| Feature | DALL-E | Hugging Face | Replicate | Firefly | Mock |
|---------|--------|--------------|-----------|---------|------|
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Speed** | 10-20s | 5-15s | 10-30s | 20-40s | <1s |
| **Cost** | $0.03/img | Free/Pro | Free+ | Free+ | Free |
| **Free Tier** | No (trial) | Yes | Yes | Yes | Yes |
| **Production Use** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **APIs Key** | Required | Required | Required | Required | No |
| **Setup Time** | <5 min | <5 min | <5 min | <5 min | 0 min |
| **Async Support** | ❌ | ❌ | ✅ | ✅ | ❌ |

---

## 🔑 API Key Management

### Setting Up Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Use DALL-E (OpenAI)
OPENAI_API_KEY=sk-...

# OR use Hugging Face
HUGGINGFACE_API_KEY=hf_...
HUGGINGFACE_MODEL=stable-diffusion-3

# OR use Replicate
REPLICATE_API_KEY=r8_...
REPLICATE_MODEL=stable-diffusion-3
```

### Security Best Practices

- ✅ Use `.env` file for local development
- ✅ Add `.env` to `.gitignore` (already done)
- ✅ Never commit API keys to version control
- ✅ Use environment variables in production
- ✅ Rotate keys regularly
- ❌ Don't hardcode keys in scripts
- ❌ Don't share `.env` files

---



- **API Keys:** Never commit `.env` to version control (use `.env.example`)
- **Generated Assets:** Saved locally; no automatic uploading
- **Logging:** Includes campaign details; review before sharing logs
- **Rate Limits:** DALL-E API has usage limits; monitor cost

---

## 📈 Performance & Costs

### Typical Performance
- **Cache hit:** < 1 second per asset
- **DALL-E generation:** 10–20 seconds per image (includes download)
- **Image processing:** < 1 second per resize
- **Full campaign:** 2 products × 3 ratios = ~60 seconds

### Estimated Costs (DALL-E 3)
- **Per image:** $0.03 (1024×1024, standard quality)
- **2 products × 3 ratios:** ~$0.18 per campaign
- **100 campaigns/month:** ~$18

---

## 🎯 Limitations & Future Work

### Current Limitations
1. **Simple cache hashing** – Basic similarity matching; no semantic grouping
2. **Single campaign per run** – CLI processes one brief at a time (batch mode is future)
3. **Provider latency and rate limits** – Generation speed depends on upstream provider performance and quota behavior
4. **Brand compliance heuristic** – Pixel sampling + keyword matching; production may need ML models for layout/object detection

### Planned Enhancements (Future)
- [ ] Batch campaign processing (CSV/Excel import)
- [ ] Multi-language text rendering (localized fonts)
- [ ] Advanced cache with semantic similarity (embeddings)
- [ ] Cloud storage integration (AWS S3, Azure Blob)
- [ ] Performance analytics dashboard
- [ ] A/B testing framework for campaign variants
- [ ] ML-based content moderation (safer content flagging)
- [ ] Image-to-image variations (e.g., style transfer)
- [ ] Authentication and role-based access control
- [ ] Webhook integration for approval workflows

---

## 🎬 Demo Recording Instructions

To record a demo video (2–3 minutes) for interviewers:

### Pre-Recording Checklist
1. ✅ Create `.env` with your OPENAI_API_KEY (or use --provider dalle)
2. ✅ Activate venv: `source venv/bin/activate`
3. ✅ Install dependencies: `pip install -e .`
4. ✅ Test CLI with a configured provider: `python -m app.main run --brief examples/sample_brief.json --provider replicate`
5. ✅ Test web UI: `python -m app.main serve` → http://localhost:8000

### Recording Content Outline

**1. Introduction (0:00–0:15)**
- Brief intro: "This is the Creative Automation Pipeline, an AI-powered tool for generating social ad creatives at scale."

**2. CLI Demo (0:15–1:00)**
```bash
# Show venv activation
source venv/bin/activate

# Show campaign brief
cat examples/sample_brief.json

# Run CLI
python -m app.main run --brief examples/sample_brief.json --provider replicate

# Show output directory
open outputs/
# Walk through product folders, aspect ratios, generated PNGs
```

**3. Web UI Demo (1:00–2:00)**
```bash
# Restart venv if needed
source venv/bin/activate

python -m app.main serve
# Open http://localhost:8000
# Fill out form (use example values)
# Trigger generation
# Show results gallery
# Show report
```

**4. Highlights (2:00–2:30)**
- Mention key features: multi-format, compliance checks, logging, caching
- Note: Can generate hundreds of variants quickly
- Show final report (costs, timing, compliance)

### Recording Tools
- **Mac:** QuickTime (`CMD+SPACE` → "QuickTime Player" → File → New Screen Recording)
- **Windows:** Xbox Game Bar (`WIN+G`)
- **Linux/Cross-platform:** OBS Studio (free)

### Tips
- **Clear narration:** Speak slowly, explain each step
- **Visible output:** Zoom in on terminal/browser (200% on Mac: System Prefs → Accessibility → Display → Resolution)
- **Logical flow:** Start simple (CLI), then interactive (web)
- **Avoid delays:** Use test generator for predictable speed

---

## 📁 Project Structure

```
poc-ai-images/
├── app/
│   ├── __init__.py              # Package init
│   ├── main.py                  # CLI + FastAPI entry point
│   ├── parsers.py               # Campaign brief validation
│   ├── generator.py             # DALL-E integration
│   ├── processor.py             # Image resizing, text overlay, logo overlay
│   ├── compliance.py            # Brand & legal checks
│   ├── storage.py               # Local file management
│   └── logger.py                # Logging & reporting
├── templates/
│   └── index.html               # Web UI (FastAPI frontend)
├── static/                       # CSS/JS assets (if cached locally)
├── examples/
│   ├── sample_brief.json        # Example JSON campaign brief
│   ├── sample_brief.yaml        # Example YAML campaign brief
│   ├── logo_brief.json          # Example brief with logo configuration
│   └── campaign_brief*.json/yaml# Additional example briefs
├── input_assets/                 # Logos & reference images for campaigns
├── outputs/
│   ├── products/                 # Generated creatives (git-ignored)
│   └── .tmp/                     # Temporary processing files (git-ignored)
├── logs/                         # Execution logs (git-ignored)
├── tests/                        # Unit & integration tests
├── pyproject.toml               # Project metadata & dependencies
├── .env.example                 # Environment template
├── .gitignore                  # Git ignore file
└── README.md                    # This file
```

---

## 🤝 Contributing

This is a PoC for demonstration purposes. For production use:

1. **Extend compliance checks** – Integrate ML-based content moderation
2. **Add cloud storage** – AWS S3, Azure Blob for asset management
3. **Database integration** – Store campaign metadata and analytics
4. **Authentication** – Add user management and API keys
5. **Webhooks** – Post-generation notifications and approvals
6. **Analytics** – Track asset performance and CTR

---

## � Troubleshooting

### Command not found: python

**Problem:** `zsh: command not found: python`

**Solution:**
```bash
# Use python3 explicitly
python3 -m app.main run --brief examples/sample_brief.json --provider dalle

# OR activate venv first (recommended)
source venv/bin/activate
python -m app.main run --brief examples/sample_brief.json --provider dalle
```

After activating venv, `python` command will work (venv has Python in its PATH).

---

### Externally-managed-environment error

**Problem:**
```
× This environment is externally managed
╰─> To install Python packages system-wide, try brew install xyz...
```

**Solution:**
This is PEP 668 protection on macOS/Homebrew. The fix is to always use a virtual environment:

```bash
# Create venv (if not already created)
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Now pip install works
pip install -r requirements.txt
```

The venv must be activated before every session. You can add an alias in `~/.zshrc`:
```bash
alias activate='source ~/path/to/poc-ai-images/venv/bin/activate'
```

Then next time just run: `activate`

---

### pip install fails

**Problem:** `error: externally-managed-environment` or permission denied

**Solution:**
1. Ensure venv is activated: `source venv/bin/activate`
2. Upgrade pip: `pip install --upgrade pip`
3. Install packages: `pip install -r requirements.txt`

**Note:** Don't use `--break-system-packages` or `sudo pip` - always use a venv.

---

### No module named 'app'

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
1. Ensure you're in the project directory: `cd poc-ai-images`
2. Ensure venv is activated: `source venv/bin/activate`
3. Reinstall package: `pip install -e .`

---

### API Key not found

**Problem:** `ValueError: OPENAI_API_KEY not found`

**Solution:**
1. Create `.env` file: `cp .env.example .env`
2. Add your API key: `OPENAI_API_KEY=sk-...`
3. Verify provider credentials in `.env` and retry with the provider you selected

---

### Web UI won't load

**Problem:** `http://localhost:8000` shows connection error

**Solution:**
1. Ensure server is running: Check terminal output for "Uvicorn running on..."
2. Try different port: `python -m app.main serve --port 8080`
3. Check if port 8000 is in use: `lsof -i :8000`
4. Refresh browser: `Cmd+Shift+R` (hard refresh)

---

## 📞 Support & Questions

For questions or issues:
1. Check the **Troubleshooting** section above first
2. Review logs: Check `logs/pipeline.log` for error details
3. Verify setup: Run `python -m app.main run --brief examples/sample_brief.json --provider dalle`
4. Check .env: Ensure `OPENAI_API_KEY` is set (or use --provider dalle)
5. Verify venv: Run `which python` - should show path to venv

---

## 📄 License

This project is provided as-is for demonstration and evaluation purposes.

---

## 🙏 Acknowledgments

Built with:
- **OpenAI DALL-E 3** – State-of-the-art image generation
- **FastAPI** – Modern Python web framework
- **Pillow** – Image processing
- **Pydantic** – Data validation

---

**Ready to generate amazing social creatives? Let's go! 🚀**

```bash
python -m app.main run --brief examples/sample_brief.json --provider dalle
```

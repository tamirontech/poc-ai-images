# HuggingFace Asset Example

## Overview

A complete example campaign brief for HuggingFace with official brand colors, comprehensive bio, and pre-generated branded logo.

## Files Created

### 1. Campaign Brief: [examples/huggingface_brief.json](examples/huggingface_brief.json)

Comprehensive HuggingFace campaign with:

**Products:**
- Hugging Face Hub
- Transformers Library  
- Model Inference

**Target:**
- **Region:** Global
- **Audience:** ML engineers, data scientists, AI researchers, open-source developers
- **Message:** "Collaborate. Build. Share. The community-first platform for machine learning."

**Brand Colors:**
1. **Gold (#FFD21E)** - Primary brand color, energy, innovation
2. **Orange (#FF9D00)** - Secondary color, warmth, approachability
3. **Gray (#6B7280)** - Neutral accent, stability, foundation

**Logo:**
- **Path:** `huggingface_logo.png` (auto-resolves to `input_assets/huggingface_logo.png`)
- **Position:** Bottom-right
- **Scale:** 0.15 (15% of image width)

**Aspect Ratios:**
- 1:1 (Square - Instagram, LinkedIn)
- 9:16 (Vertical - TikTok, Reels, Stories)
- 16:9 (Wide - YouTube, Presentations)

**Campaign Context:**

> Hugging Face is the collaboration platform for the machine learning community. The Hugging Face Hub works as a central place where anyone can share, explore, discover, and experiment with open-source ML. HF empowers the next generation of machine learning engineers, scientists, and end users to learn, collaborate and share their work to build an open and ethical AI future together. With the fast-growing community, some of the most used open-source ML libraries and tools, and a talented science team exploring the edge of tech, Hugging Face is at the heart of the AI revolution. Visual style: Modern, inclusive, community-driven. Emphasize collaboration, open-source values, and cutting-edge AI technology. Show diverse developers, global connectivity, and shared innovation.

---

### 2. Branded Logo: [input_assets/huggingface_logo.png](input_assets/huggingface_logo.png)

**Specifications:**
- **Dimensions:** 500 × 500 pixels
- **Format:** PNG with transparency (RGBA)
- **File Size:** ~2-3 KB
- **Colors:** Uses HuggingFace official brand colors

**Design Elements:**

The logo uses a modern, symbolic design:

```
    Top Node (Orange)
         ↓
    ┌─────────────────┐
    │  Outer (Gold)   │
    │   ┌───────────┐ │
    │   │ Inner     │ │
Left │   │ (Orange)  │ │ Right
Node ├─→ │ ┌───────┐ │ ← Node
    │   │ │ Center │ │
    │   │ │ (Gray)  │ │
    │   └───────────┘ │
    └─────────────────┘
         ↑
    Bottom Node (Orange)
```

**Symbolism:**
- **Outer Circle (Gold):** Main brand, core identity, leadership
- **Inner Circle (Orange):** Innovation, evolution, forward-thinking
- **Center (Gray):** Stability, foundation, trust
- **Surrounding Nodes:** Global community, collaboration, connectivity

**Generation Script:**
- Script: [create_hf_logo.py](create_hf_logo.py)
- Uses Pillow (PIL) for image generation
- Colors defined as constants at top of script
- Easy to regenerate or modify

---

## Color Palette

| Color | Hex | RGB | Usage | Symbolism |
|-------|-----|-----|-------|-----------|
| **Gold** | #FFD21E | (255, 210, 30) | Primary brand color | Energy, innovation, leadership |
| **Orange** | #FF9D00 | (255, 157, 0) | Secondary, highlights | Warmth, approachability, growth |
| **Gray** | #6B7280 | (107, 114, 128) | Accents, text | Stability, professionalism, trust |

---

## Usage

### Basic Usage

```bash
# Generate campaign with mock provider (no API key needed)
python -m app.main run --brief examples/huggingface_brief.json --provider dalle

# Generate with DALL-E
python -m app.main run --brief examples/huggingface_brief.json --provider dalle

# Generate with HuggingFace provider
python -m app.main run --brief examples/huggingface_brief.json --provider huggingface
```

### Expected Output

```
outputs/
├── Hugging Face Hub/
│   ├── 1-1/
│   │   ├── Hugging Face Hub_1-1_*.png        (Generated image)
│   │   └── Hugging Face Hub_1-1_input_*.png  (From input asset)
│   ├── 9-16/
│   │   └── *.png
│   └── 16-9/
│       └── *.png
├── Transformers Library/
│   ├── 1-1/
│   ├── 9-16/
│   └── 16-9/
├── Model Inference/
│   ├── 1-1/
│   ├── 9-16/
│   └── 16-9/
└── report_20260308_220000.{json,html}
```

### Generated Assets

Each product will have **9 image variations:**
- 3 products × 3 aspect ratios = 9 images

**With Logo:**
- All images include HuggingFace logo in bottom-right (15% scale)
- Logo overlay applied using Pillow image processing

**With Brand Colors:**
- All API prompts include guidance on HuggingFace brand colors
- Generators instructed to use gold, orange, and gray prominently
- Modern, minimalist aesthetic emphasized

---

## Customization

### Modify Logo

Edit [create_hf_logo.py](create_hf_logo.py):

```python
# Change colors
GOLD = "#FFD21E"      # Primary
ORANGE = "#FF9D00"    # Secondary
GRAY = "#6B7280"      # Accent

# Run to regenerate
python create_hf_logo.py
```

### Modify Campaign

Edit [examples/huggingface_brief.json](examples/huggingface_brief.json):

```json
{
  "products": [...],                    // Change products
  "target_region": "...",               // Target market
  "brand_colors": ["#...", ...],        // Brand colors
  "additional_context": "...",          // Campaign context
  "aspect_ratios": ["1:1", ...]        // Image sizes
}
```

---

## Asset System Integration

This example demonstrates the complete asset system:

### Input → Generation → Output Flow

```
input_assets/
└── huggingface_logo.png
         ↓
    [Campaign Processing]
         ↓
outputs/
├── .tmp/                    (Temporary API downloads)
│   └── dalle_Hub_*.png
├── Hugging Face Hub/
│   ├── 1-1/
│   │   └── *.png           (Final optimized images)
│   ├── 9-16/
│   └── 16-9/
└── report_*.{json,html}    (Campaign report)
```

### Key Features Used

✅ **Logo Path Resolution:** `"logo_path": "huggingface_logo.png"` → Auto-resolves to `input_assets/huggingface_logo.png`

✅ **Asset Reuse:** Logo is applied to all generated images

✅ **Brand Integration:** Colors included in generation prompts

✅ **Organized Output:** All results in `outputs/{product}/{aspect-ratio}/`

✅ **Comprehensive Reporting:** JSON + HTML reports with metrics

---

## Brand Guidelines Summary

### Visual Identity

- **Style:** Modern, minimalist, inclusive
- **Palette:** Gold (primary) + Orange (secondary) + Gray (neutral)
- **Logo:** Symbolic circles representing community & collaboration
- **Typography:** Clean, professional, accessible

### Messaging

- **Core Message:** Community-driven ML platform
- **Tone:** Collaborative, innovative, trustworthy
- **Values:** Open-source, ethical AI, shared knowledge

### Applications

All generated assets should:
- Feature the gold/orange/gray color scheme
- Convey collaboration and open-source values
- Show diversity and global community
- Emphasize cutting-edge AI technology
- Be suitable for:
  - Social media (Instagram, LinkedIn, TikTok)
  - Presentations and documentation
  - Marketing campaigns
  - Community communications

---

## File Summary

| File | Purpose | Size |
|------|---------|------|
| `examples/huggingface_brief.json` | Campaign definition | ~2 KB |
| `input_assets/huggingface_logo.png` | Branded logo | ~3 KB |
| `create_hf_logo.py` | Logo generation script | ~2 KB |
| `validate_hf_example.py` | Validation script | ~1.5 KB |

---

## Next Steps

1. **Generate Campaign:**
   ```bash
   python -m app.main run --brief examples/huggingface_brief.json --provider dalle
   ```

2. **Review Outputs:**
   ```bash
   open outputs/  # View generated images
   open outputs/report_*.html  # View campaign report
   ```

3. **Use Real API (Optional):**
   - Set OPENAI_API_KEY or HF_API_KEY
   - Use `--provider dalle` or `--provider huggingface`

4. **Customize:**
   - Modify brief.json for different campaign variations
   - Update logo colors in create_hf_logo.py
   - Add additional products or regions

---

## Technical Details

### Brief Validation

The brief is automatically validated at parse time:

```python
from app.parsers import BriefParser

# This will:
# ✓ Validate all required fields
# ✓ Resolve logo path to input_assets/
# ✓ Check logo file exists
# ✓ Validate aspect ratios
# ✓ Ensure colors are valid hex codes
brief = BriefParser.parse_file("examples/huggingface_brief.json")
```

### Image Generation

For each product and aspect ratio:

1. **Check for Input Asset:**
   - Look in `input_assets/` for pre-existing images
   - Use if found (saves API cost)

2. **Check Cache:**
   - Look in `outputs/{product}/{aspect-ratio}/`
   - Use if found (previously generated)

3. **Generate New:**
   - Call selected generator (DALL-E, HuggingFace, etc.)
   - Download to `outputs/.tmp/`
   - Apply logo overlay (from input_assets)
   - Apply text overlays (brand message)
   - Resize to target aspect ratio
   - Save to `outputs/{product}/{aspect-ratio}/`

4. **Report:**
   - Track cost, time, success/failure
   - Generate JSON and HTML reports

---

## Example Report Output

```json
{
  "campaign_id": "hf_example_20260308",
  "campaign_message": "Collaborate. Build. Share...",
  "total_products": 3,
  "total_aspect_ratios": 3,
  "total_assets": 9,
  "assets_generated": 9,
  "assets_from_input": 0,
  "assets_from_cache": 0,
  "estimated_cost_usd": 0.18,
  "processing_time_seconds": 45.2,
  "status": "completed",
  "products": {
    "Hugging Face Hub": {
      "1-1": {
        "status": "success",
        "asset_path": "outputs/Hugging Face Hub/1-1/...",
        "cached": false
      },
      ...
    }
  }
}
```

---

## Support

For questions or issues:

1. Check [ASSET_SYSTEM.md](ASSET_SYSTEM.md) for asset management details
2. Review [README.md](README.md) for general usage
3. Check `app/parsers.py` for brief format validation
4. Check `app/main.py` for pipeline logic

---

**Created:** March 8, 2026  
**Version:** 1.0  
**Status:** Ready for Production

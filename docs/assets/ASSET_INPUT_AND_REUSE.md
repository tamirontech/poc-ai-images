# Asset Input & Reuse System

**Problem Solved:** Skip expensive GenAI generation when you already have quality assets!

## 🎯 How It Works (3-Level Fallback Strategy)

```
Asset Request (Product + Region + Message + Aspect Ratio)
    ↓
Level 1: Check for Exact Cached Match
    → Found? ✓ Reuse ($0, <100ms)
    → Not found? Continue...
    ↓
Level 2: Check for User Input Asset  
    → Found? ✓ Reuse user file ($0, <100ms)
    → Not found? Continue...
    ↓
Level 3: Generate New Asset
    → Call GenAI API (~$0.03, 10-30s)
    → Process (resize, text, logo)
    → Cache for future reuse
    ↓
Asset Ready (from any source)
```

## 📁 Directory Structure

### Input Assets (User-Provided)

```
input_assets/
├── EcoSoap.png                 ← Exact product match
├── NaturalShampoo.jpg          ← Supported formats
├── ProductAlternative_input.png ← With _input suffix
└── OtherProduct_source.jpg      ← With _source suffix
```

**Naming Convention:** `{product}.{ext}` or `{product}_input.{ext}` or `{product}_source.{ext}`

**Supported Formats:** `.png`, `.jpg`, `.jpeg`

### Generated Assets (Cached)

```
outputs/
└── products/
    ├── EcoSoap/
    │   ├── 1-1/                    ← Aspect ratio folders
    │   │   ├── EcoSoap_1-1_1706987234.png
    │   │   └── EcoSoap_1-1_input_1706987245.png  ← Input asset cached here
    │   ├── 9-16/
    │   │   └── EcoSoap_9-16_1706987250.png
    │   └── 16-9/
    │       └── EcoSoap_16-9_1706987255.png
    └── NaturalShampoo/
        ├── 1-1/
        └── 9-16/
```

## ✨ Key Features

### 1. **Automatic Input Asset Detection**

Place files in `input_assets/` folder with product name:

```bash
mkdir -p input_assets
cp my_ecosoap_photo.png input_assets/EcoSoap.png
```

Pipeline automatically finds and uses them!

### 2. **Smart Caching**

- **First run with input asset:** Processes + caches it
- **Second run same product:** Reuses cached version (instant)
- **Different product:** Generates new or checks for its input asset

### 3. **Fallback Generation**

If no input asset exists → Generates new one via GenAI → Caches for future

### 4. **Processing Applied to All Sources**

Regardless of source (input, cache, or generated):
- ✅ Resized to target aspect ratio
- ✅ Text overlay added (campaign message)
- ✅ Logo overlay added (if provided)
- ✅ Branded for consistency

## 📊 Example: Cost & Time Comparison

| Scenario | Source | Cost | Time | How? |
|----------|--------|------|------|------|
| First run, have asset | Input | $0 | ~2s | Copy + process |
| Second run, no API | Cache | $0 | <1s | Load + process cached |
| Third run, new product | Generate | $0.03 | 15s | DALL-E + cache |
| Fourth run, same product | Cache | $0 | <1s | Reuse cached |

## 🚀 Usage Examples

### Example 1: Use Input Assets Only (No API Costs)

```bash
# 1. Add images to input_assets/
mkdir -p input_assets
cp my_photos/eco_soap.png input_assets/EcoSoap.png
cp my_photos/shampoo.jpg input_assets/NaturalShampoo.jpg

# 2. Create campaign brief (same products)
cat > brief.json << 'EOF'
{
  "products": ["EcoSoap", "NaturalShampoo"],
  "target_region": "Japan",
  "target_audience": "Eco-conscious professionals",
  "campaign_message": "Sustainable self-care",
  "logo_path": "./input_assets/sample_logo.png"
}
EOF

# 3. Run pipeline
source venv/bin/activate
python -m app.main run --brief brief.json

# Result: ✓ Uses input assets, adds text + logo, caches them
# Cost: $0 (no API calls)
# Time: ~5 seconds total
```

### Example 2: Hybrid (Input + Generated)

```bash
# Input assets for 2 products
input_assets/
├── EcoSoap.png
└── NaturalShampoo.jpg

# Brief has 3 products
{
  "products": ["EcoSoap", "NaturalShampoo", "EcoBrush"]
}

# Run pipeline
python -m app.main run --brief brief.json

# Result:
# ✓ EcoSoap: Uses input asset (cached after first run)
# ✓ NaturalShampoo: Uses input asset (cached after first run)
# ✗ EcoBrush: Generates via DALL-E (no input asset)
```

### Example 3: Test Input Assets Before Sending to API

```bash
# Test processing without API calls
python -m app.main run --brief brief.json --provider dalle
# Uses test generator for other products
# But still uses input assets where available

# Then run with real API when ready
python -m app.main run --brief brief.json
```

### Example 4: List Available Input Assets

```python
from app.asset_manager import AssetInputManager

manager = AssetInputManager()
print(manager.get_input_asset_info())

# Output:
# Input Assets in ./input_assets:
#   • EcoSoap: EcoSoap.png (245.3 KB)
#   • NaturalShampoo: NaturalShampoo.jpg (189.5 KB)
```

## 🔍 Asset Resolution (How Pipeline Decides)

**For each product + aspect ratio combination:**

```python
# Step 1: Check for cached match
if cached_asset_for_product_ratio_exists:
    use_cached  # Most recent file in outputs/{product}/{ratio}/

# Step 2: Check for user input asset
elif input_asset_for_product_exists:
    copy_to_cache(input_asset)
    use_copied    # Add text + logo overlays

# Step 3: Generate new
else:
    generate_via_api()
    cache_result()
    use_generated  # Add text + logo overlays
```

**Key Points:**
- **Exact matches first** → Look for cached asset with same product/region/message/ratio
- **Input fallback** → Look for user-provided file in `input_assets/`
- **Generate last** → Only call API if nothing found

## 📝 Campaign Brief Integration

You can explicitly mark that you're providing input assets:

```json
{
  "products": ["EcoSoap", "NaturalShampoo"],
  "target_region": "Japan",
  "target_audience": "Eco-conscious millennials",
  "campaign_message": "Sustainable self-care for a better tomorrow",
  "language": "en",
  "brand_colors": ["#2D5016", "#FFFFFF", "#FFD700"],
  "logo_path": "./input_assets/sample_logo.png",
  "additional_context": "Input assets provided in ./input_assets folder - will be reused if available, generated if missing"
}
```

## 🔧 Pipeline Logging

When you run the pipeline, you'll see:

```
Processing campaign: Japan | Products: EcoSoap, NaturalShampoo
  Processing product: EcoSoap
    Aspect ratio: 1:1
      ✓ Using input asset: EcoSoap.png              ← Input asset found!
      Cached input asset: outputs/EcoSoap/1-1/...
    Aspect ratio: 9:16
      ✓ Using cached asset: EcoSoap_9-16_...png    ← Cached from first run
    Aspect ratio: 16:9
      Generating image via DALL-E...                ← New generation
      ✓ Saved: outputs/EcoSoap/16-9/...png
  
  Processing product: NaturalShampoo
    Aspect ratio: 1:1
      ✓ Using cached asset: NaturalShampoo_1-1_...png ← From input_assets, now cached
```

## 📊 AssetInputManager API

```python
from app.asset_manager import AssetInputManager

manager = AssetInputManager(
    input_dir="./input_assets",   # Where users put files
    cache_dir="./outputs"          # Where generated assets go
)

# Check for asset with 3-level fallback
asset_path, source = manager.get_asset_with_fallback(
    product="EcoSoap",
    region="Japan",
    message="Sustainable self-care",
    aspect_ratio="1:1"
)

# Returns:
# - asset_path: Path to file (if found)
# - source: one of "cached:ratio", "input", or None

# List all available input assets
assets = manager.list_input_assets()
# {"EcoSoap": Path("input_assets/EcoSoap.png"), ...}

# Get info about inputs
print(manager.get_input_asset_info())

# Validate input file
is_valid, msg = manager.validate_input_asset(Path("input_assets/EcoSoap.png"))

# Copy input to cache with proper naming
cached_path = manager.copy_input_to_cache(
    input_asset=Path("input_assets/EcoSoap.png"),
    product="EcoSoap",
    aspect_ratio="1:1"
)
```

## ✅ File Validation

Input assets are validated:

✅ **File must exist**
✅ **Format must be PNG, JPG, or JPEG**
✅ **Size must be 10 KB - 50 MB**

```python
is_valid, message = manager.validate_input_asset(file_path)
if not is_valid:
    print(f"Invalid asset: {message}")
```

## 🎯 Use Cases

### Case 1: Product Photography Campaign

```
You have professional product photos
    ↓ Place in input_assets/
    ↓ Create campaign brief with product names
    ↓ Run with --provider dalle (test) or with API
    ↓ Assets processed (resized, text overlay, logo)
    ↓ Reused for multiple aspects/regions
```

**Saving:** Skip expensive GenAI entirely! Use your own assets.

### Case 2: Iterative Design

```
Run 1: Use DALL-E to generate initial creative
    ↓ Review in outputs/
Run 2: Move good one to input_assets/ with product name
    ↓ Re-run campaign with new brand colors
    ↓ Asset reused with new branding
```

**Benefit:** Improve assets without re-generating

### Case 3: Mixed Strategy

```
Have input assets for 3 products
Need new creative for 2 new products

Run 1: Place 3 input assets in input_assets/
Run 2: Brief includes all 5 products
    → 3 reuse input assets
    → 2 generate via GenAI
    → All cached for future
```

**Saving:** Only generate what you need

## 🚀 Advanced: Batch Processing

```python
from app.asset_manager import AssetInputManager
from app.main import CreativeAutomationPipeline

# Setup
pipeline = CreativeAutomationPipeline(provider="dalle")
manager = pipeline.asset_manager

# See what's available
print(manager.get_input_asset_info())

# Process multiple briefs
for brief_file in ["brief1.json", "brief2.json", "brief3.json"]:
    from app.parsers import BriefParser
    brief = BriefParser.parse_file(brief_file)
    results = pipeline.process_campaign(brief)
    
    # Results automatically include asset sources
    print(f"Campaign results: {results}")
```

## 📈 Performance Impact

### Without Input Assets
```
3 products × 3 ratios = 9 images
9 × $0.03 = $0.27 cost
9 × 15 seconds = 135 seconds (~2 min)
```

### With Input Assets + Caching
```
Run 1: 3 products × 3 ratios = 2 input, 1 generated
       Cost: $0.03, Time: ~20 seconds
Run 2: 3 products × 3 ratios = 3 cached
       Cost: $0, Time: ~3 seconds
Run 3: 3 products × 3 ratios = 3 cached
       Cost: $0, Time: ~3 seconds

9 runs same campaign: $0.03 + $0 × 8 = $0.03 total
```

**Savings: 90% cost reduction, 97% time reduction!**

## 📝 Integration with CI/CD

```bash
# .github/workflows/generate-creatives.yml
- name: Generate Campaign Creatives
  run: |
    # Assets checked in to repo
    mkdir -p input_assets && git lfs pull
    
    # Generate with smart reuse
    python -m app.main run --brief campaigns/current.json
    
    # Commit new cached assets
    git add outputs/
    git commit -m "Generated creatives with smart caching"
```

## 🎨 Logo & Text Still Applied

Even when using input assets:

```
Input Asset (EcoSoap.png)
    ↓ Resize to aspect ratio (1:1, 9:16, 16:9)
    ↓ Add campaign message text overlay
    ↓ Add logo (if provided)
    ↓ Final branded creative
```

Every asset gets consistent branding treatment!

## 🔐 File Organization Tips

**Recommended:**
```
project/
├── input_assets/          ← All user-provided images, logos, brand elements
│   ├── EcoSoap.png
│   ├── NaturalShampoo.jpg
│   ├── EcoBrush.png
│   └── sample_logo.png
└── outputs/
    └── products/          ← Generated + processed
        ├── EcoSoap/
        ├── NaturalShampoo/
        └── EcoBrush/
```

**DO:**
- ✅ Place input assets in `input_assets/`
- ✅ Name them after product names
- ✅ Keep high-quality originals
- ✅ Commit input_assets to version control

**DON'T:**
- ❌ Mix outputs/ and input_assets/
- ❌ Upload outputs/ to assets folder
- ❌ Name files inconsistently

## 🐛 Troubleshooting

### Input asset not being found
```
✗ Check: File named {product}.png in ./input_assets/
✗ Check: Spelling matches brief product name exactly
✗ Check: File format is .png, .jpg, or .jpeg
✗ Check: File is >10 KB and <50 MB
```

### Asset reused as input but then uses cached version
```
✓ Expected behavior!
  Run 1: input_assets/EcoSoap.png → copied to cache
  Run 2: Uses cached version (faster)
  Run 3+: Always uses cache
```

### All assets still being generated (not using inputs)

```python
# Debug: Check if assets are found
from app.asset_manager import AssetInputManager
manager = AssetInputManager()
assets = manager.list_input_assets()
print(f"Found {len(assets)} input assets: {list(assets.keys())}")
```

## 📊 Report Information

The final report includes asset source for each generated asset:

```json
{
  "products": {
    "EcoSoap": [
      {
        "aspect_ratio": "1:1",
        "status": "success",
        "file_path": "outputs/EcoSoap/1-1/...",
        "cached": true,          ← Indicates reused from cache/input
        "asset_source": "input"  ← Shows where it came from
      }
    ]
  }
}
```

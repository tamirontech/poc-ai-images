# Prompt Engineering & API Parameter Flow

This document explains how campaign brief details translate into API requests across all supported image generation providers.

## 📋 Campaign Brief → API Request Flow

### Input: Campaign Brief (JSON/YAML)

```json
{
  "products": ["EcoSoap"],
  "target_region": "Japan",
  "target_audience": "Young professionals, eco-conscious millennials",
  "campaign_message": "Sustainable self-care for a better tomorrow",
  "language": "en",
  "brand_colors": ["#2D5016", "#FFFFFF", "#FFD700"],
  "aspect_ratios": ["1:1", "9:16", "16:9"],
  "additional_context": "Modern, minimalist design with natural elements",
  "logo_path": "./input_assets/sample_logo.png",
  "logo_position": "bottom-right",
  "logo_scale": 0.15
}
```

### Processing Pipeline

```
CampaignBrief (Parsed)
        ↓
Compliance Check (brand message validation)
        ↓
_build_prompt() → Comprehensive Text Prompt
        ↓ (Parameters: product, region, audience, message, context, colors, logo_path, logo_position)
        ↓
generate_image() [API-specific implementation]
        ↓
Image downloaded/saved locally
        ↓
process_image() [Pillow]
        ├─ Resize to aspect ratio
        ├─ Add text overlay
        └─ Add logo overlay
        ↓
Output: Processed PNG image
```

## 🎯 Comprehensive Prompt Generation

### Method: `_build_prompt()`

**Input Parameters:**
- `product`: Product name → Used in opening phrase
- `region`: Target market → "Target market:" guidance
- `audience`: Audience description → "Target audience:" guidance
- `message`: Campaign message → "Campaign message:" in quotes
- `additional_context`: Style/mood hints → Appended as final context
- `brand_colors`: Color hex codes → Color guidance with exact hex values
- `logo_path`: Path to logo file → Logo positioning hint
- `logo_position`: Where logo goes → Corner/center guidance

### Generated Prompt Structure

The prompt is assembled as follows:

1. **Core Creative Brief**
   ```
   Create a professional, modern social media advertisement for {product}
   ```

2. **Market Context**
   ```
   Target market: {region}
   Target audience: {audience}
   Campaign message: '{message}'
   ```

3. **Style Guidance**
   ```
   Style: vibrant, engaging, on-brand, high-quality
   Professional product photography with modern design elements
   Suitable for social media (Instagram, TikTok, LinkedIn, Facebook)
   ```

4. **Brand Colors** (if provided)
   ```
   Use brand colors prominently: #2D5016, #FFFFFF, #FFD700
   ```

5. **Logo Positioning** (if logo_path provided)
   ```
   Design with {logo_position} space reserved for brand logo.
   Ensure visual balance and avoid crowding that area.
   ```

6. **Additional Context** (if provided)
   ```
   Additional context: {additional_context}
   ```

7. **Critical Instruction**
   ```
   Do not include any text overlays or captions
   ```

### Example Complete Prompt

```
Create a professional, modern social media advertisement for EcoSoap. 
Target market: Japan. 
Target audience: Young professionals, eco-conscious millennials. 
Campaign message: 'Sustainable self-care for a better tomorrow'. 
Style: vibrant, engaging, on-brand, high-quality. 
Professional product photography with modern design elements. 
Suitable for social media (Instagram, TikTok, LinkedIn, Facebook). 
Use brand colors prominently: #2D5016, #FFFFFF, #FFD700. 
Design with bottom-right space reserved for brand logo. 
Ensure visual balance and avoid crowding that area. 
Additional context: Modern, minimalist design with natural elements. 
Do not include any text overlays or captions.
```

## 🔌 API-Specific Implementation

All providers receive the **same parameters** and build from the **same prompt**:

### 1️⃣ DALL-E 3 (OpenAI)

**Method Signature:**
```python
def generate_image(
    self,
    product: str,
    region: str,
    audience: str,
    message: str,
    additional_context: str = "",
    size: str = "1024x1024",
    brand_colors: Optional[List[str]] = None,
    logo_path: Optional[str] = None,
    logo_position: str = "bottom-right",
    logo_scale: float = 0.15,
) -> str:
```

**API Request Payload:**
```json
{
  "model": "dall-e-3",
  "prompt": "[full prompt with brand colors and logo positioning]",
  "n": 1,
  "size": "1024x1024",
  "quality": "standard"
}
```

**Note:** Logo is applied **after** generation by `processor.process_image()`

**Endpoint:** `https://api.openai.com/v1/images/generations`

---

### 2️⃣ Hugging Face Inference API

**Method Signature:**
```python
def generate_image(
    self,
    product: str,
    region: str,
    audience: str,
    message: str,
    additional_context: str = "",
    size: str = "1024x1024",  # Ignored by HF
    brand_colors: Optional[List[str]] = None,
    logo_path: Optional[str] = None,
    logo_position: str = "bottom-right",
    logo_scale: float = 0.15,
) -> str:
```

**Available Models:**
- `stable-diffusion-3` (default) → Best balance
- `flux-dev` → Highest quality
- `flux-schnell` → Fastest

**API Request Payload:**
```json
{
  "inputs": "[full prompt with brand colors and logo positioning]"
}
```

**Endpoint:** `https://api-inference.huggingface.co/models/{model_id}`

**Response:** Binary image data (PNG/JPEG)

---

### 3️⃣ Replicate API

**Method Signature:**
```python
def generate_image(
    self,
    product: str,
    region: str,
    audience: str,
    message: str,
    additional_context: str = "",
    size: str = "1024x1024",
    brand_colors: Optional[List[str]] = None,
    logo_path: Optional[str] = None,
    logo_position: str = "bottom-right",
    logo_scale: float = 0.15,
) -> str:
```

**Available Models:**
- `stable-diffusion-3`
- `flux-dev`
- `flux-schnell`

**API Request Payload:**
```json
{
  "version": "stability-ai/stable-diffusion-3",
  "input": {
    "prompt": "[full prompt with brand colors and logo positioning]",
    "width": 1024,
    "height": 1024
  }
}
```

**Endpoint (Create):** `https://api.replicate.com/v1/predictions`

**Behavior:** Async polling with max 5-minute timeout

**Response:** URL to generated image

---

### 4️⃣ DALL-E Provider (Testing)

**Method Signature:**
```python
def generate_image(
    self,
    product: str,
    region: str,
    audience: str,
    message: str,
    additional_context: str = "",
    size: str = "1024x1024",
    brand_colors: Optional[List[str]] = None,  # Ignored
    logo_path: Optional[str] = None,           # Ignored
    logo_position: str = "bottom-right",       # Ignored
    logo_scale: float = 0.15,                  # Ignored
) -> str:
```

**Behavior:**
- Generates placeholder blue rectangle
- Embed product/region/message text
- No API calls
- Instant generation (<100ms)
- **Perfect for testing logo & text overlay logic without costs**

**Response:** Local file path to mock PNG

---

## 🔄 Parameter Usage Summary

| Parameter | Type | Used In | How It's Used |
|-----------|------|---------|---------------|
| `product` | str | Prompt | Opening phrase: "advertisement for {product}" |
| `region` | str | Prompt | Market guidance: "Target market: {region}" |
| `audience` | str | Prompt | Audience targeting: "Target audience: {audience}" |
| `message` | str | Prompt + Text Overlay | Prompt: "Campaign message: '{message}'" + Pillow overlay |
| `additional_context` | str | Prompt | Style/mood hints appended to prompt |
| `brand_colors` | List[str] | Prompt | Color guidance: "Use brand colors: #2D5016, #FFFFFF" |
| `logo_path` | str | Prompt + Processor | Prompt: positioning hints + Pillow overlay after generation |
| `logo_position` | str | Prompt + Processor | Prompt: "Design with bottom-right space reserved" + overlay position |
| `logo_scale` | float | Processor | Pillow: resizes logo to this % of image width |
| `size` | str | API Payload | DALL-E/Replicate only; aspect ratio request |
| `language` | str | Campaign memo | Not sent to API (could be added for localization) |

## ✅ Compliance & Validation

**Before Prompt Generation:**

1. **Message Compliance Check**
   - Validates `message` against prohibited words
   - Examples: "free", "guaranteed", "miracle", "clinically proven"
   - Logged as warnings but doesn't block generation

2. **Brand Color Validation**
   - Parsers validate hex format (#RRGGBB)
   - Colors stored as strings in brief

3. **Logo Path Validation**
   - Path existence checked in `processor._add_logo_overlay()`
   - File type validation (PNG/JPG)
   - Transparency preserved if available

## 🚀 Practical Examples

### Example 1: DALL-E with Full Branding

```python
from app.parsers import BriefParser
from app.generator import DALLEImageGenerator
from app.processor import ImageProcessor
from app.storage import StorageManager

# Parse brief
brief = BriefParser.parse_file("campaigns/eco_beauty.json")

# Create generator
generator = DALLEImageGenerator()

# Generate (includes brand colors + logo positioning guidance)
image_url = generator.generate_image(
    product=brief.products[0],           # "EcoSoap"
    region=brief.target_region,          # "Japan"
    audience=brief.target_audience,      # "Young professionals..."
    message=brief.campaign_message,      # "Sustainable self-care..."
    additional_context=brief.additional_context,
    brand_colors=brief.brand_colors,     # ["#2D5016", "#FFFFFF", "#FFD700"]
    logo_path=brief.logo_path,           # "./assets/logo.png"
    logo_position=brief.logo_position,   # "bottom-right"
    logo_scale=brief.logo_scale          # 0.15
)

# Download & process
temp_file = f"/tmp/dalle_{product}.png"
generator.download_image(image_url, temp_file)

# Add logo + text overlay
processor = ImageProcessor()
processed = processor.process_image(
    temp_file,
    aspect_ratio="1:1",
    overlay_text=brief.campaign_message,
    logo_path=brief.logo_path,
    logo_position=brief.logo_position,
    logo_scale=brief.logo_scale
)
```

### Example 2: Testing with Mock (No API Costs)

```python
# Same code, but with mock:
from app.generator import MockImageGenerator

generator = MockImageGenerator()
temp_file = generator.generate_image(
    product=brief.products[0],
    region=brief.target_region,
    audience=brief.target_audience,
    message=brief.campaign_message,
    additional_context=brief.additional_context,
    brand_colors=brief.brand_colors,
    logo_path=brief.logo_path,
    logo_position=brief.logo_position,
    logo_scale=brief.logo_scale
)
# Returns instantly - no API call needed!
```

### Example 3: Testing Prompt Quality

```python
from app.generator import MockImageGenerator

generator = MockImageGenerator()
prompt = generator._build_prompt(
    product="EcoSoap",
    region="Japan",
    audience="Young professionals",
    message="Sustainable self-care",
    additional_context="Minimalist design",
    brand_colors=["#2D5016", "#FFFFFF"],
    logo_path="./assets/logo.png",
    logo_position="bottom-right"
)

print(prompt)
# See exactly what will be sent to any API
```

## 📊 Parameter Flow Diagram

```
Campaign Brief JSON
    ├─ products → generate_image(product=...)
    ├─ target_region → generate_image(region=...)
    ├─ target_audience → generate_image(audience=...)
    ├─ campaign_message → generate_image(message=...) + process_image(overlay_text=...)
    ├─ additional_context → generate_image(additional_context=...)
    ├─ brand_colors → generate_image(brand_colors=...) → Prompt guidance
    ├─ logo_path → generate_image(logo_path=...) → Prompt guidance + process_image(logo_path=...)
    ├─ logo_position → generate_image(logo_position=...) → Prompt guidance + process_image(logo_position=...)
    └─ logo_scale → process_image(logo_scale=...) → Pillow overlay sizing

API Call (DALL-E/HF/Replicate)
    ↓ (receives full prompt with brand context)
Generated Image
    ↓
Processor (Pillow)
    ├─ Resize to aspect ratio
    ├─ Add campaign message as text overlay
    ├─ Add logo with positioning/scale
    └─ Output: Branded creative ready for social media
```

## 🎨 Why This Matters

1. **Consistency:** All APIs receive the same prompt structure
2. **Brand Safety:** Colors and logo positioning guidance sent to all providers
3. **Smart Default:** If colors/logo/context not provided, prompt still works
4. **No API Lock-in:** Switch providers without changing brief format
5. **Compliance:** Message validation happens before any API call
6. **Flexibility:** Each provider interprets guidance in its own style

## 📝 Configuration Checklist

Before generating:

- [ ] Campaign message is compliant (no prohibited words)
- [ ] Brand colors are valid hex codes (e.g., #2D5016)
- [ ] Logo file exists if logo_path specified
- [ ] Logo is PNG with transparency (for clean overlay)
- [ ] Logo position is one of: top-left, top-right, bottom-left, bottom-right, center
- [ ] Logo scale is between 0.1-0.5 (10-50% of image width)
- [ ] API key is set for chosen provider (OPENAI_API_KEY, HUGGINGFACE_API_KEY, etc.)

## 🔗 Example Briefs

See [examples/logo_brief.json](examples/logo_brief.json) for a complete example with all parameters.

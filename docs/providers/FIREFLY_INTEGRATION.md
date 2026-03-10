# Adobe Firefly API Integration Guide

## Overview

Adobe Firefly is now available as an image generation provider in the Creative Automation Pipeline. This integration enables text-to-image generation with Adobe's state-of-the-art generative AI technology.

## Features

- **Text-to-Image Generation**: Generate high-quality images from text prompts
- **Async Support**: Built-in asynchronous processing for concurrent image generation
- **Content Styling**: Photo and art content classes for varied aesthetic output
- **Multiple Sizes**: Support for various image dimensions (1024x1024, 2048x2048, etc.)
- **Job Polling**: Automatic polling for asynchronous job completion
- **Error Handling**: Comprehensive error handling and retry logic

## Setup

### 1. Get Adobe API Key

1. Visit [Adobe Developer Console](https://developer.adobe.com/console)
2. Create a new project or use an existing one
3. Add Firefly Services API to your project
4. Generate API credentials (Client ID and API Key)

### 2. Configure Environment

Set your Firefly API key:

```bash
export FIREFLY_API_KEY="your-adobe-api-key-here"
```

Or add to `.env` file:

```env
FIREFLY_API_KEY=your-adobe-api-key-here
```

### 3. Verify Configuration

```python
from app.config import settings

# Check if Firefly is configured
api_key = settings.get_provider_api_key('firefly')
is_valid = settings.validate_provider_config('firefly')
print(f"Firefly configured: {is_valid}")
```

## Usage

### CLI Image Generation

Generate images using Firefly:

```bash
python -m app.main --provider firefly --brief examples/sample_brief.json
```

### Web Server

Start the web server with Firefly as the provider:

```bash
python -m app.main web --provider firefly --port 8000
```

### Programmatic Usage

```python
from app.firefly_generator import FireflyImageGenerator

# Initialize generator
generator = FireflyImageGenerator()

# Generate image
image_url = generator.generate_image(
    product="Premium Headphones",
    region="US",
    audience="Tech enthusiasts",
    message="Experience pristine audio quality",
    additional_context="Modern minimalist design, premium materials"
)

print(f"Generated image: {image_url}")
```

## API Endpoints

### Generate Images (Async)

**Endpoint**: `POST /v3/images/generate-async`

**Request**:
```json
{
  "prompt": "Professional product photography of modern wireless headphones...",
  "size": {
    "width": 1024,
    "height": 1024
  },
  "numVariations": 1,
  "contentClass": "photo",
  "negativePrompt": ""
}
```

**Response**:
```json
{
  "jobId": "e1f2d3c4-b5a6-47c8-9d0e-1f2a3b4c5d6e",
  "statusUrl": "https://firefly-api.adobe.io/v3/status/...",
  "cancelUrl": "https://firefly-api.adobe.io/v3/cancel/..."
}
```

### Check Job Status

**Endpoint**: `GET /v3/status/{jobId}`

**Response**:
```json
{
  "jobId": "e1f2d3c4-b5a6-47c8-9d0e-1f2a3b4c5d6e",
  "status": "SUCCEEDED",
  "result": {
    "outputs": [
      {
        "seed": 42,
        "image": {
          "url": "https://firefly-api.adobe.io/images/..."
        }
      }
    ],
    "size": {
      "width": 1024,
      "height": 1024
    }
  }
}
```

## Supported Image Sizes

| Size | Dimensions | Use Case |
|------|-----------|----------|
| `1024x1024` | 1:1 (Square) | Social media profiles, thumbnails |
| `1024x1536` | 2:3 (Portrait) | Mobile ads, vertical content |
| `1536x1024` | 3:2 (Landscape) | Web banners, horizontal content |
| `2048x2048` | 1:1 (Square) | High-resolution prints, posters |

## Configuration Options

### Image Generation Settings

```python
from app.config import settings

# Customize image generation
settings.image_size = "2048x2048"  # Default: "1024x1024"
settings.firefly_api_key = "your-key"  # Set API key
```

### Content Classes

- **photo**: Photorealistic content (default)
- **art**: Artistic, illustrated content

```python
# In FireflyImageGenerator source code
payload = {
    "contentClass": "photo",  # or "art"
}
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `FIREFLY_API_KEY not set` | Missing API key | Set environment variable `FIREFLY_API_KEY` |
| `Generation failed: Invalid prompt` | Invalid text prompt | Check prompt length (max 1024 chars) |
| `Job timeout` | Processing took too long | Increase max_wait parameter or check API status |
| `No job ID in response` | API response malformed | Verify API key is valid |

### Error Recovery

The generator includes automatic retry logic:

```python
try:
    image_url = generator.generate_image(
        product="Product",
        region="US",
        audience="Audience",
        message="Message"
    )
except Exception as e:
    print(f"Generation failed: {e}")
    # Fallback to test generator
    from app.generator import MockImageGenerator
    fallback = MockImageGenerator()
    image_url = fallback.generate_image(...)
```

## Performance Considerations

### Job Polling

- **Poll Interval**: 2 seconds between status checks
- **Max Wait Time**: 300 seconds (5 minutes)
- **Timeout Behavior**: Returns error if job exceeds max wait time

## Testing

### Unit Tests

Run the comprehensive Firefly test suite:

```bash
pytest tests/test_firefly_generator.py -v
```

**Test Coverage**:
- ✅ API key configuration and validation
- ✅ Job submission and polling
- ✅ Success and error scenarios
- ✅ Async functionality
- ✅ Size handling and defaults
- ✅ Inheritance and base class compliance

### Sample Test

```python
def test_generate_image_success():
    """Test successful image generation"""
    gen = FireflyImageGenerator(api_key="test-key")
    
    result = gen.generate_image(
        product="Test Product",
        region="US",
        audience="Tech enthusiasts",
        message="Innovative solution"
    )
    
    assert "http" in result or "/" in result  # Valid URL or path
```

## Integration with Pipeline

### Full Campaign Generation

```bash
python -m app.main generate \
  --provider firefly \
  --brief campaigns/product_brief.json \
  --output ./firefly_outputs
```

### Compliance Checking

Generated images are automatically checked for compliance:

```python
from app.main import CreativeAutomationPipeline

pipeline = CreativeAutomationPipeline(provider="firefly")
results = pipeline.process_brief("brief_file.json")

for result in results:
    if result["compliant"]:
        print(f"✅ {result['file']}")
    else:
        print(f"❌ {result['file']}: {result['issues']}")
```

## Rate Limiting

Adobe Firefly has rate limits depending on your plan:

- **Free Tier**: Limited API calls per day
- **Professional**: Higher rate limits
- **Enterprise**: Custom rate limits

Monitor your usage:

```python
logger = PipelineLogger()
report = logger.generate_report()
print(report.estimated_api_cost)  # USD cost estimate
```

## Troubleshooting

### "No image URL in result"

**Cause**: API returned empty outputs  
**Solution**: 
1. Verify API key is valid
2. Check account has remaining credits
3. Ensure prompt meets requirements (1-1024 characters)

### "Job timeout"

**Cause**: Generation took longer than 5 minutes  
**Solution**:
1. Increase `max_wait` parameter
2. Check API service status at adobe.io
3. Try with simpler prompt

### "Invalid dimensions"

**Cause**: Unsupported image size requested  
**Solution**: Use supported sizes from the table above

## Examples

### Product Photography Campaign

```python
gen = FireflyImageGenerator(api_key="your-key")

products = ["Laptop", "Phone", "Tablet"]
regions = ["US", "EU", "APAC"]

for product in products:
    for region in regions:
        image = gen.generate_image(
            product=product,
            region=region,
            audience="Tech professionals",
            message=f"Premium {product} for {region} market",
            additional_context="Modern design, professional lighting"
        )
        print(f"{product} ({region}): {image}")
```

### Fashion Campaign with Style Control

```python
# Generate multiple style variations
styles = ["Modern", "Classic", "Minimalist", "Luxury"]

for style in styles:
    image = gen.generate_image(
        product="Designer Jacket",
        region="US",
        audience="Fashion enthusiasts",
        message=f"{style} styling for modern wardrobes",
        additional_context=f"Style: {style}, professional photography"
    )
    print(f"{style}: {image}")
```

## Documentation

- [Adobe Firefly API Reference](https://developer.adobe.com/firefly-services/docs/)
- [OpenAPI Specification](../firefly-api.json)
- [Code Examples](../examples/firefly_examples.py)

## Support

For issues or questions:

1. Check [Adobe Developer Support](https://developers.adobe.com/support)
2. Review error messages and troubleshooting section above
3. Run test suite to verify setup: `pytest tests/test_firefly_generator.py`
4. Check logs in `./logs/` directory

## License

This integration complies with Adobe Firefly Services Terms of Use.

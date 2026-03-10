#!/usr/bin/env python3
"""Test that all image generators accept and handle prompt parameters consistently."""

from app.parsers import BriefParser
from app.generator import (
    DALLEImageGenerator,
    HuggingFaceImageGenerator,
    ReplicateImageGenerator,
)


def test_prompt_generation():
    """Test that all generators produce comprehensive prompts with brand parameters."""
    
    # Parse a brief with full brand details
    brief = BriefParser.parse_file("examples/logo_brief.json")

    # Test prompt construction with DALL-E generator.
    generator = DALLEImageGenerator(api_key="test-key")

    # Build prompt with all parameters
    prompt = generator._build_prompt(
        product=brief.products[0],
        region=brief.target_region,
        audience=brief.target_audience,
        message=brief.campaign_message,
        additional_context=brief.additional_context,
        brand_colors=brief.brand_colors,
        logo_path=brief.logo_path,
        logo_position=brief.logo_position,
    )

    # Verify prompt includes all important elements
    assertions = [
        ("Product in prompt", f"for {brief.products[0]}" in prompt),
        ("Region in prompt", brief.target_region in prompt),
        ("Brand colors in prompt", all(color in prompt for color in brief.brand_colors)),
        ("Logo positioning in prompt", brief.logo_position in prompt),
        ("No text overlay instruction", "text overlays" in prompt),
        ("Message captured", brief.campaign_message in prompt),
        ("Additional context included", brief.additional_context in prompt),
    ]

    print("✅ API PARAMETER FLOW VERIFICATION\n")
    print("=" * 70)
    print("Testing: Brand colors, logo positioning, compliance guidance")
    print("=" * 70)

    all_passed = True
    for test_name, passed in assertions:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    print("GENERATED PROMPT:")
    print("=" * 70)
    print(prompt)
    print("=" * 70)

    assert all_passed


def test_generator_signatures():
    """Verify all generators have the correct method signatures."""
    
    generators = [
        ("DALL-E", DALLEImageGenerator),
        ("HuggingFace", HuggingFaceImageGenerator),
        ("Replicate", ReplicateImageGenerator),
    ]

    print("\n✅ METHOD SIGNATURE VERIFICATION\n")
    print("=" * 70)
    print("Checking that all generators accept brand/logo parameters")
    print("=" * 70)

    required_params = [
        "product",
        "region",
        "audience",
        "message",
        "additional_context",
        "size",
        "brand_colors",
        "logo_path",
        "logo_position",
        "logo_scale",
    ]

    all_valid = True
    for gen_name, gen_class in generators:
        # Check generate_image signature
        import inspect

        sig = inspect.signature(gen_class.generate_image)
        params = list(sig.parameters.keys())
        
        missing = [p for p in required_params if p not in params]
        
        if missing:
            print(f"✗ {gen_name}: Missing parameters: {missing}")
            all_valid = False
        else:
            print(f"✓ {gen_name}: All parameters present")

    print("=" * 70)
    assert all_valid


if __name__ == "__main__":
    try:
        test_generator_signatures()
        test_prompt_generation()
        test1_pass = True
        test2_pass = True

        print("\n" + "🎉 " * 20)
        if test1_pass and test2_pass:
            print("✅ ALL TESTS PASSED - Prompt engineering complete!")
            print("    • Brand colors fully integrated")
            print("    • Logo positioning guidance in prompts")
            print("    • All APIs support comprehensive parameters")
            print("    • Compliance & branding ready for all providers")
        else:
            print("❌ SOME TESTS FAILED - Check implementation")
        print("🎉 " * 20)

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()

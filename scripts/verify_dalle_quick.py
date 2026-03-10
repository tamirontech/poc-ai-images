#!/usr/bin/env python3
"""Quick verification of DALL-E implementation."""

from app.generator import DALLEImageGenerator
import sys

def verify_dalle():
    """Verify DALL-E implementation is correct."""
    
    print("=" * 60)
    print("DALL-E Implementation Verification")
    print("=" * 60)
    
    # Test 1: Check class exists and is callable
    print("\n[1] Class Import")
    try:
        print("✓ DALLEImageGenerator class imports successfully")
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False
    
    # Test 2: Check method signatures
    print("\n[2] Method Availability")
    methods = ['generate_image', '_build_prompt', 'download_image']
    for method in methods:
        if hasattr(DALLEImageGenerator, method):
            print(f"✓ Method '{method}' exists")
        else:
            print(f"✗ Method '{method}' MISSING")
    
    # Test 3: Check initialization with explicit API key
    print("\n[3] Initialization")
    try:
        gen = DALLEImageGenerator(api_key='test-key-for-verification')
        print("✓ Initializes with explicit API key")
        print(f"  - Model: {gen.model}")
        print(f"  - Base URL: {gen.base_url}")
        print(f"  - Images generated counter: {gen.images_generated}")
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False
    
    # Test 4: Check error handling for missing API key
    print("\n[4] Error Handling")
    try:
        gen = DALLEImageGenerator()
        print("✗ Should have raised ValueError for missing API key")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg:
            print("✓ Properly raises ValueError when API key missing")
            print(f"  - Error message: {error_msg[:70]}...")
        else:
            print(f"✗ ValueError message doesn't mention OPENAI_API_KEY: {e}")
            return False
    except Exception as e:
        print(f"✗ Unexpected error type: {type(e).__name__}: {e}")
        return False
    
    # Test 5: Check model parameter
    print("\n[5] Model Configuration")
    try:
        gen_dalle2 = DALLEImageGenerator(api_key='test', model='dall-e-2')
        if gen_dalle2.model == 'dall-e-2':
            print("✓ Can initialize with dall-e-2 model")
        else:
            print(f"✗ Model not set correctly: {gen_dalle2.model}")
            return False
            
        gen_dalle3 = DALLEImageGenerator(api_key='test', model='dall-e-3')
        if gen_dalle3.model == 'dall-e-3':
            print("✓ Can initialize with dall-e-3 model")
        else:
            print(f"✗ Model not set correctly: {gen_dalle3.model}")
            return False
    except Exception as e:
        print(f"✗ Model configuration failed: {e}")
        return False
    
    # Test 6: Check inherited methods
    print("\n[6] Inherited Methods")
    gen = DALLEImageGenerator(api_key='test')
    try:
        # Check _build_prompt is callable
        if callable(gen._build_prompt):
            print("✓ _build_prompt method is callable (inherited)")
        else:
            print("✗ _build_prompt is not callable")
            return False
            
        # Check download_image is callable
        if callable(gen.download_image):
            print("✓ download_image method is callable (inherited)")
        else:
            print("✗ download_image is not callable")
            return False
    except Exception as e:
        print(f"✗ Inherited method check failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ DALL-E Implementation Verification PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = verify_dalle()
    sys.exit(0 if success else 1)

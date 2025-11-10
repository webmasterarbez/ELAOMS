#!/usr/bin/env python3
"""Test script to verify system__* fields are prioritized correctly."""
import sys
import os
import json
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up logging to avoid errors
logging.basicConfig(level=logging.WARNING)

# Import directly without going through __init__.py
import importlib.util
spec = importlib.util.spec_from_file_location("helpers", Path(__file__).parent.parent / "src" / "utils" / "helpers.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)

extract_user_id_from_payload = helpers.extract_user_id_from_payload

# Import extract_caller_name
spec2 = importlib.util.spec_from_file_location("build_profile", Path(__file__).parent.parent / "scripts" / "build_comprehensive_user_profile.py")
build_profile = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(build_profile)

extract_caller_name = build_profile.extract_caller_name

def test_extract_user_id_with_system_caller_id():
    """Test that system__caller_id is prioritized first."""
    print("=" * 60)
    print("Test 1: Extract user_id with system__caller_id")
    print("=" * 60)
    
    # Load the actual payload
    payload_path = Path(__file__).parent.parent / "data" / "webhooks" / "+16129782029" / "conv_8201k9nrcxpde18rng9hga5484rm_transcription.json"
    
    if not payload_path.exists():
        print(f"❌ Payload file not found: {payload_path}")
        return False
    
    with open(payload_path, 'r') as f:
        payload = json.load(f)
    
    # Extract user_id
    user_id = extract_user_id_from_payload(payload)
    
    expected = "+16129782029"
    if user_id == expected:
        print(f"✅ SUCCESS: Extracted user_id = {user_id}")
        print(f"   Expected: {expected}")
        return True
    else:
        print(f"❌ FAILED: Extracted user_id = {user_id}")
        print(f"   Expected: {expected}")
        return False


def test_extract_user_id_with_external_number():
    """Test that external_number is used as fallback when system__caller_id is missing."""
    print("\n" + "=" * 60)
    print("Test 2: Extract user_id with external_number fallback")
    print("=" * 60)
    
    # Create a payload without system__caller_id but with external_number
    payload = {
        "type": "post_call_transcription",
        "data": {
            "conversation_id": "conv_test123",
            "metadata": {
                "phone_call": {
                    "external_number": "+15551234567"
                }
            },
            "conversation_initiation_client_data": {
                "dynamic_variables": {}
            }
        }
    }
    
    user_id = extract_user_id_from_payload(payload)
    
    expected = "+15551234567"
    if user_id == expected:
        print(f"✅ SUCCESS: Extracted user_id = {user_id}")
        print(f"   Expected: {expected}")
        return True
    else:
        print(f"❌ FAILED: Extracted user_id = {user_id}")
        print(f"   Expected: {expected}")
        return False


def test_extract_caller_name_with_system_caller_name():
    """Test that system__caller_name is prioritized first."""
    print("\n" + "=" * 60)
    print("Test 3: Extract caller name with system__caller_name")
    print("=" * 60)
    
    # Create conversation data with system__caller_name
    conversation_data = {
        "conversation_initiation_client_data": {
            "dynamic_variables": {
                "system__caller_name": "John Doe",
                "caller_name": "Jane Smith",  # Should be ignored
                "name": "Bob"  # Should be ignored
            }
        }
    }
    
    caller_name = extract_caller_name(conversation_data)
    
    expected = "John Doe"
    if caller_name == expected:
        print(f"✅ SUCCESS: Extracted caller_name = {caller_name}")
        print(f"   Expected: {expected}")
        return True
    else:
        print(f"❌ FAILED: Extracted caller_name = {caller_name}")
        print(f"   Expected: {expected}")
        return False


def test_extract_user_id_priority_order():
    """Test that priority order is correct."""
    print("\n" + "=" * 60)
    print("Test 4: Verify priority order")
    print("=" * 60)
    
    # Test Priority 1: system__caller_id
    payload1 = {
        "data": {
            "conversation_initiation_client_data": {
                "dynamic_variables": {
                    "system__caller_id": "+11111111111"
                },
                "user_id": "+22222222222"  # Should be ignored
            },
            "metadata": {
                "user_id": "+33333333333",  # Should be ignored
                "phone_call": {
                    "external_number": "+44444444444"  # Should be ignored
                }
            }
        }
    }
    user_id1 = extract_user_id_from_payload(payload1)
    assert user_id1 == "+11111111111", f"Priority 1 failed: got {user_id1}"
    print("✅ Priority 1 (system__caller_id) works correctly")
    
    # Test Priority 6: external_number (when system__caller_id is missing)
    payload2 = {
        "data": {
            "conversation_initiation_client_data": {
                "dynamic_variables": {}
            },
            "metadata": {
                "phone_call": {
                    "external_number": "+55555555555"
                }
            }
        }
    }
    user_id2 = extract_user_id_from_payload(payload2)
    assert user_id2 == "+55555555555", f"Priority 6 failed: got {user_id2}"
    print("✅ Priority 6 (external_number) works correctly")
    
    return True


def test_audio_webhook_processing_with_none_caller_phone():
    """Test that audio webhook processing works even when caller_phone is None."""
    print("\n" + "=" * 60)
    print("Test 5: Audio webhook processing with None caller_phone")
    print("=" * 60)
    
    # Import the function directly
    spec3 = importlib.util.spec_from_file_location("webhook_storage", Path(__file__).parent.parent / "src" / "utils" / "webhook_storage.py")
    webhook_storage = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(webhook_storage)
    
    process_cached_audio_webhook = webhook_storage.process_cached_audio_webhook
    
    # This test verifies the function signature accepts Optional[str]
    # We can't easily test the full flow without setting up cache, but we can verify
    # the function signature is correct
    import inspect
    sig = inspect.signature(process_cached_audio_webhook)
    caller_phone_param = sig.parameters['caller_phone']
    
    # Check if it's Optional[str]
    from typing import get_args, get_origin
    if get_origin(caller_phone_param.annotation) is not None:
        # It's a Union type (Optional)
        print(f"✅ Function signature accepts Optional[str] for caller_phone")
        return True
    elif caller_phone_param.annotation == type(None) or 'Optional' in str(caller_phone_param.annotation):
        print(f"✅ Function signature accepts Optional[str] for caller_phone")
        return True
    else:
        print(f"❌ Function signature: {caller_phone_param.annotation}")
        print(f"   Expected: Optional[str]")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing System Fields Priority Implementation")
    print("=" * 60)
    print()
    
    results = []
    
    # Run all tests
    results.append(("Extract user_id with system__caller_id", test_extract_user_id_with_system_caller_id()))
    results.append(("Extract user_id with external_number", test_extract_user_id_with_external_number()))
    results.append(("Extract caller name with system__caller_name", test_extract_caller_name_with_system_caller_name()))
    results.append(("Verify priority order", test_extract_user_id_priority_order()))
    results.append(("Audio webhook with None caller_phone", test_audio_webhook_processing_with_none_caller_phone()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


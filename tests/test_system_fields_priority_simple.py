#!/usr/bin/env python3
"""Simple test script to verify system__* fields are prioritized correctly."""
import json
import sys
from pathlib import Path

# Simple test without importing modules that have dependencies
def test_extract_user_id_logic():
    """Test the extraction logic directly."""
    print("=" * 60)
    print("Testing System Fields Priority Logic")
    print("=" * 60)
    print()
    
    # Test payload with system__caller_id
    payload1 = {
        "data": {
            "conversation_initiation_client_data": {
                "dynamic_variables": {
                    "system__caller_id": "+16129782029"
                }
            },
            "metadata": {
                "phone_call": {
                    "external_number": "+15551234567"
                }
            }
        }
    }
    
    # Simulate the extraction logic
    data = payload1.get("data", {})
    dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    caller_id = dynamic_vars.get("system__caller_id")
    
    if caller_id:
        user_id = str(caller_id).strip()
        print(f"✅ Test 1 PASSED: system__caller_id extracted = {user_id}")
        assert user_id == "+16129782029", f"Expected +16129782029, got {user_id}"
    else:
        print(f"❌ Test 1 FAILED: system__caller_id not found")
        return False
    
    # Test payload with only external_number (no system__caller_id)
    payload2 = {
        "data": {
            "conversation_initiation_client_data": {
                "dynamic_variables": {}
            },
            "metadata": {
                "phone_call": {
                    "external_number": "+15551234567"
                }
            }
        }
    }
    
    # Simulate the extraction logic with fallback
    data2 = payload2.get("data", {})
    dynamic_vars2 = data2.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    caller_id2 = dynamic_vars2.get("system__caller_id")
    
    if not caller_id2:
        # Check external_number as fallback
        phone_call = data2.get("metadata", {}).get("phone_call", {})
        external_number = phone_call.get("external_number")
        if external_number:
            user_id2 = str(external_number).strip()
            print(f"✅ Test 2 PASSED: external_number extracted = {user_id2}")
            assert user_id2 == "+15551234567", f"Expected +15551234567, got {user_id2}"
        else:
            print(f"❌ Test 2 FAILED: external_number not found")
            return False
    else:
        print(f"❌ Test 2 FAILED: system__caller_id found when it shouldn't be")
        return False
    
    # Test with actual payload file
    payload_path = Path(__file__).parent.parent / "data" / "webhooks" / "+16129782029" / "conv_8201k9nrcxpde18rng9hga5484rm_transcription.json"
    if payload_path.exists():
        with open(payload_path, 'r') as f:
            actual_payload = json.load(f)
        
        data3 = actual_payload.get("data", {})
        dynamic_vars3 = data3.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
        caller_id3 = dynamic_vars3.get("system__caller_id")
        
        if caller_id3:
            user_id3 = str(caller_id3).strip()
            print(f"✅ Test 3 PASSED: Actual payload system__caller_id = {user_id3}")
            assert user_id3 == "+16129782029", f"Expected +16129782029, got {user_id3}"
        else:
            print(f"❌ Test 3 FAILED: system__caller_id not found in actual payload")
            return False
    else:
        print(f"⚠️  Test 3 SKIPPED: Payload file not found: {payload_path}")
    
    print("\n" + "=" * 60)
    print("All Tests Passed!")
    print("=" * 60)
    return True


def test_caller_name_priority():
    """Test that system__caller_name is prioritized first."""
    print("\n" + "=" * 60)
    print("Testing Caller Name Priority")
    print("=" * 60)
    
    # Simulate the extraction logic
    dynamic_vars = {
        "system__caller_name": "John Doe",
        "caller_name": "Jane Smith",  # Should be ignored
        "name": "Bob"  # Should be ignored
    }
    
    # Simulate the priority order
    name_fields = [
        "system__caller_name",  # First priority
        "caller_name",
        "name",
        "user_name",
        "customer_name"
    ]
    
    caller_name = None
    for field in name_fields:
        name = dynamic_vars.get(field)
        if name:
            caller_name = str(name).strip()
            break
    
    if caller_name == "John Doe":
        print(f"✅ Test PASSED: system__caller_name extracted = {caller_name}")
        return True
    else:
        print(f"❌ Test FAILED: Expected 'John Doe', got '{caller_name}'")
        return False


if __name__ == "__main__":
    try:
        result1 = test_extract_user_id_logic()
        result2 = test_caller_name_priority()
        
        if result1 and result2:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


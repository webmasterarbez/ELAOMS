#!/usr/bin/env python3
"""Test script to send a saved payload through the post-call webhook endpoint."""
import requests
import json
import hmac
import hashlib
import time
import sys
from pathlib import Path
from config import settings

def generate_hmac_signature(timestamp: int, payload: str, secret: str) -> str:
    """Generate HMAC signature for the webhook.
    
    Note: The server uses timestamp as a string (from header), so we convert to string
    to match the exact format the server expects.
    """
    # Convert timestamp to string to match server's format (server uses string from header)
    timestamp_str = str(timestamp)
    payload_to_sign = f"{timestamp_str}.{payload}"
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    )
    return f"t={timestamp},v0={mac.hexdigest()}"

def test_post_call_webhook(payload_file: str, webhook_url: str = "http://localhost:8000/webhooks/post-call"):
    """Test the post-call webhook endpoint with a saved payload file.
    
    Args:
        payload_file: Path to the saved payload JSON file
        webhook_url: URL of the webhook endpoint (default: http://localhost:8000/webhooks/post-call)
    """
    print("=" * 60)
    print("Testing Post-Call Webhook with Saved Payload")
    print("=" * 60)
    print()
    
    # Load the payload file
    payload_path = Path(payload_file)
    if not payload_path.exists():
        print(f"❌ ERROR: Payload file not found: {payload_file}")
        return False
    
    try:
        with open(payload_path, 'r') as f:
            payload_data = json.load(f)
        print(f"✓ Loaded payload from: {payload_file}")
        print(f"  Conversation ID: {payload_data.get('data', {}).get('conversation_id', 'N/A')}")
        print(f"  Agent ID: {payload_data.get('data', {}).get('agent_id', 'N/A')}")
        print(f"  Type: {payload_data.get('type', 'N/A')}")
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON in payload file: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: Failed to load payload file: {e}")
        return False
    
    # Check if webhook secret is configured
    if not settings.elevenlabs_post_call_hmac_key:
        print("❌ ERROR: ELEVENLABS_POST_CALL_HMAC_KEY is not configured in .env file!")
        print("   Please set ELEVENLABS_POST_CALL_HMAC_KEY in your .env file.")
        return False
    
    # Use current timestamp (not the one from the payload, as it may be in the future)
    timestamp = int(time.time())
    print(f"✓ Using current timestamp: {timestamp}")
    
    # Convert payload to JSON string (compact format to match ElevenLabs format)
    payload_json = json.dumps(payload_data, separators=(',', ':'))
    print(f"✓ Payload size: {len(payload_json)} bytes")
    
    # Generate HMAC signature
    signature = generate_hmac_signature(
        timestamp=timestamp,
        payload=payload_json,
        secret=settings.elevenlabs_post_call_hmac_key
    )
    
    print(f"✓ Generated HMAC signature")
    print(f"  Signature prefix: {signature[:50]}...")
    print()
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "elevenlabs-signature": signature,
        "User-Agent": "ElevenLabs/1.0"
    }
    
    print("=" * 60)
    print("Sending POST request to webhook endpoint")
    print("=" * 60)
    print(f"URL: {webhook_url}")
    print(f"Headers: {list(headers.keys())}")
    print()
    
    try:
        # Send POST request
        response = requests.post(
            webhook_url,
            json=payload_data,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook processed successfully!")
            try:
                response_data = response.json()
                if 'memory_id' in response_data:
                    print(f"   Memory ID: {response_data['memory_id']}")
                if 'status' in response_data:
                    print(f"   Status: {response_data['status']}")
            except:
                pass
            return True
        else:
            print(f"❌ ERROR: Webhook failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to webhook endpoint: {webhook_url}")
        print("   Make sure the server is running on the specified URL.")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ ERROR: Request timed out after 30 seconds")
        return False
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Default payload file path
    default_payload_file = "data/webhooks/+16129782029/conv_9901k9n0k6b2ean81hyedp2hdsn7_transcription.json"
    
    # Get payload file from command line argument or use default
    if len(sys.argv) > 1:
        payload_file = sys.argv[1]
    else:
        payload_file = default_payload_file
    
    # Get webhook URL from command line argument or use default
    webhook_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000/webhooks/post-call"
    
    print(f"Payload file: {payload_file}")
    print(f"Webhook URL: {webhook_url}")
    print()
    
    success = test_post_call_webhook(payload_file, webhook_url)
    
    print()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed. Check the error messages above.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


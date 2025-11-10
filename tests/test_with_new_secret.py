#!/usr/bin/env python3
"""Test webhook with a newly generated signature using the current secret."""
import requests
import hmac
import hashlib
import time
import json
from config import settings

# Use a simplified payload for testing
test_payload = {
    "type": "post_call_transcription",
    "event_timestamp": int(time.time()),
    "data": {
        "agent_id": "agent_5001k9myfdmae9ntkrhxfr5b4tqy",
        "conversation_id": "conv_6601k9mywx20fxcbpyv2wtff3zph",
        "status": "done"
    }
}

def generate_hmac_signature(timestamp: int, payload: str, secret: str) -> str:
    """Generate HMAC signature for the webhook."""
    timestamp_str = str(timestamp)
    payload_to_sign = f"{timestamp_str}.{payload}"
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    )
    return f"t={timestamp},v0={mac.hexdigest()}"

def test_webhook():
    """Test the webhook endpoint with a newly generated signature."""
    url = "http://localhost:8000/webhooks/post-call"
    
    # Serialize payload to JSON string (matching exact format)
    payload_json = json.dumps(test_payload, separators=(',', ':'))
    
    # Generate signature with current timestamp
    timestamp = int(time.time())
    signature_header = generate_hmac_signature(
        timestamp=timestamp,
        payload=payload_json,
        secret=settings.elevenlabs_post_call_hmac_key
    )
    
    headers = {
        "Content-Type": "application/json",
        "elevenlabs-signature": signature_header,
        "User-Agent": "ElevenLabs/1.0"
    }
    
    print("=" * 60)
    print("Testing Post-Call Webhook with New Signature")
    print("=" * 60)
    print()
    print(f"HMAC key configured: {'Yes' if settings.elevenlabs_post_call_hmac_key else 'No'}")
    if settings.elevenlabs_post_call_hmac_key:
        print(f"HMAC key length: {len(settings.elevenlabs_post_call_hmac_key)}")
        print(f"HMAC key ends with: ...{settings.elevenlabs_post_call_hmac_key[-10:]}")
    print()
    print(f"URL: {url}")
    print(f"Timestamp: {timestamp}")
    print(f"Signature: {signature_header[:50]}...")
    print(f"Payload: {payload_json[:100]}...")
    print()
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=payload_json.encode('utf-8'),
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS: Webhook authenticated and processed!")
            try:
                response_data = response.json()
                if "memory_id" in response_data:
                    print(f"Memory ID: {response_data['memory_id']}")
            except:
                pass
            return True
        elif response.status_code == 401:
            print("❌ FAILED: Authentication failed")
            print()
            print("Possible issues:")
            print("1. Server not restarted - Restart server to load new secret from .env")
            print("2. Secret mismatch - Verify ELEVENLABS_POST_CALL_HMAC_KEY in .env matches ElevenLabs")
            print("3. Timestamp validation - Check server logs for timestamp errors")
            return False
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to webhook endpoint.")
        print("Make sure the server is running: python main.py")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_webhook()
    print()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
        print()
        print("The authentication code is working correctly!")
        print("Note: The old payload won't work because it was signed with the old secret.")
        print("You'll need new webhooks from ElevenLabs that are signed with the new secret.")
    else:
        print("❌ Test failed. Check the error messages above.")
        print()
        print("Important:")
        print("1. Restart the server to load the new secret: kill <pid> && python main.py")
        print("2. The old payload signature won't match - it was signed with the old secret")
        print("3. You need new webhooks from ElevenLabs signed with the new secret")
    print("=" * 60)


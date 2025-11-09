#!/usr/bin/env python3
"""Test script to directly call the post-call webhook function with a saved payload."""
import json
import asyncio
import time
import hmac
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock
from fastapi import Request, BackgroundTasks
from config import settings
from src.webhooks.post_call import post_call_webhook

def generate_hmac_signature(timestamp: int, payload: str, secret: str) -> str:
    """Generate HMAC signature for the webhook."""
    timestamp_str = str(timestamp)
    payload_to_sign = f"{timestamp_str}.{payload}"
    mac = hmac.new(
        key=secret.encode("utf-8"),
        msg=payload_to_sign.encode("utf-8"),
        digestmod=sha256
    )
    return f"t={timestamp},v0={mac.hexdigest()}"

def create_mock_request(payload_data: Dict[str, Any], signature: str) -> Request:
    """Create a mock FastAPI Request object with the payload and signature."""
    # Convert payload to JSON string
    payload_json = json.dumps(payload_data, separators=(',', ':'))
    payload_bytes = payload_json.encode('utf-8')
    
    # Create a mock request
    mock_request = Mock(spec=Request)
    mock_request.body = Mock(return_value=payload_bytes)
    mock_request.headers = {
        "elevenlabs-signature": signature,
        "content-type": "application/json",
        "user-agent": "ElevenLabs/1.0"
    }
    mock_request.client = Mock()
    mock_request.client.host = "127.0.0.1"
    
    # Make body() async
    async def async_body():
        return payload_bytes
    
    mock_request.body = async_body
    
    return mock_request

async def test_post_call_webhook_direct(payload_file: str):
    """Test the post-call webhook function directly with a saved payload file.
    
    Args:
        payload_file: Path to the saved payload JSON file
    """
    print("=" * 60)
    print("Testing Post-Call Webhook Function Directly")
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
    
    # Use current timestamp
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
    
    # Create mock request
    mock_request = create_mock_request(payload_data, signature)
    background_tasks = BackgroundTasks()
    
    print("=" * 60)
    print("Calling post_call_webhook function")
    print("=" * 60)
    print()
    
    try:
        # Call the webhook function directly
        response = await post_call_webhook(mock_request, background_tasks)
        
        print("✅ SUCCESS: Webhook processed successfully!")
        print(f"Response: {response}")
        print()
        
        # Run background tasks
        if background_tasks.tasks:
            print(f"Running {len(background_tasks.tasks)} background task(s)...")
            await background_tasks()
            print("✓ Background tasks completed")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Webhook failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    # Default payload file path
    default_payload_file = "data/webhooks/+16129782029/conv_9901k9n0k6b2ean81hyedp2hdsn7_transcription.json"
    
    # Get payload file from command line argument or use default
    if len(sys.argv) > 1:
        payload_file = sys.argv[1]
    else:
        payload_file = default_payload_file
    
    print(f"Payload file: {payload_file}")
    print()
    
    success = asyncio.run(test_post_call_webhook_direct(payload_file))
    
    print()
    print("=" * 60)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed. Check the error messages above.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


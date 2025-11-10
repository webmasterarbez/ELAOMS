#!/usr/bin/env python3
"""Load all payloads from a directory and process them through the post-call webhook system."""
import json
import asyncio
import time
import hmac
import sys
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock
from fastapi import Request, BackgroundTasks

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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
    
    # Create headers dict
    headers_dict = {
        "elevenlabs-signature": signature,
        "content-type": "application/json",
        "user-agent": "ElevenLabs/1.0"
    }
    
    # Create a mock request
    mock_request = Mock(spec=Request)
    
    # Create a mock headers object that supports .get()
    mock_headers = Mock()
    mock_headers.get = lambda key, default=None: headers_dict.get(key, default)
    mock_request.headers = mock_headers
    
    mock_request.client = Mock()
    mock_request.client.host = "127.0.0.1"
    
    # Make body() async
    async def async_body():
        return payload_bytes
    
    mock_request.body = async_body
    
    return mock_request

async def process_payload(payload_file: Path) -> tuple:
    """Process a single payload file through the post-call webhook system.
    
    Args:
        payload_file: Path to the payload JSON file
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Load the payload file
        with open(payload_file, 'r') as f:
            raw_payload = json.load(f)
        
        # Check if payload already has webhook structure (type and data fields)
        if 'type' in raw_payload and 'data' in raw_payload:
            # Already in webhook format
            payload_data = raw_payload
        else:
            # Wrap in webhook format - assume it's a transcription webhook
            # Check if it has transcript field to determine type
            if 'transcript' in raw_payload:
                webhook_type = 'post_call_transcription'
            elif 'full_audio' in raw_payload:
                webhook_type = 'post_call_audio'
            elif 'error' in raw_payload or 'error_code' in raw_payload:
                webhook_type = 'call_initiation_failure'
            else:
                # Default to transcription if we can't determine
                webhook_type = 'post_call_transcription'
            
            payload_data = {
                'type': webhook_type,
                'data': raw_payload
            }
        
        conversation_id = payload_data.get('data', {}).get('conversation_id', 'N/A')
        agent_id = payload_data.get('data', {}).get('agent_id', 'N/A')
        webhook_type = payload_data.get('type', 'N/A')
        
        # Check if webhook secret is configured
        if not settings.elevenlabs_post_call_hmac_key:
            return False, "ELEVENLABS_POST_CALL_HMAC_KEY is not configured"
        
        # Use current timestamp
        timestamp = int(time.time())
        
        # Convert payload to JSON string (compact format to match ElevenLabs format)
        payload_json = json.dumps(payload_data, separators=(',', ':'))
        
        # Generate HMAC signature
        signature = generate_hmac_signature(
            timestamp=timestamp,
            payload=payload_json,
            secret=settings.elevenlabs_post_call_hmac_key
        )
        
        # Create mock request
        mock_request = create_mock_request(payload_data, signature)
        background_tasks = BackgroundTasks()
        
        # Call the webhook function directly
        response = await post_call_webhook(mock_request, background_tasks)
        
        # Run background tasks
        if background_tasks.tasks:
            await background_tasks()
        
        memory_id = response.get('memory_id', 'N/A') if isinstance(response, dict) else 'N/A'
        return True, f"Success - Memory ID: {memory_id}"
        
    except Exception as e:
        return False, f"Error: {str(e)}"

async def load_all_payloads(directory: str):
    """Load and process all payload files from a directory.
    
    Args:
        directory: Directory path containing payload files
    """
    print("=" * 80)
    print("Loading All Payloads Through Post-Call Webhook System")
    print("=" * 80)
    print()
    
    # Check if webhook secret is configured
    if not settings.elevenlabs_post_call_hmac_key:
        print("❌ ERROR: ELEVENLABS_POST_CALL_HMAC_KEY is not configured in .env file!")
        print("   Please set ELEVENLABS_POST_CALL_HMAC_KEY in your .env file.")
        return
    
    # Find all payload files
    payload_dir = Path(directory)
    if not payload_dir.exists():
        print(f"❌ ERROR: Directory not found: {directory}")
        return
    
    # Find all files matching the pattern (conv_*_payload.json)
    payload_files = list(payload_dir.glob("conv_*_payload.json"))
    
    if not payload_files:
        print(f"❌ No payload files found in {directory}")
        print(f"   Looking for files matching pattern: conv_*_payload.json")
        return
    
    print(f"✓ Found {len(payload_files)} payload file(s)")
    print()
    
    # Process each payload
    results = []
    for i, payload_file in enumerate(payload_files, 1):
        print(f"[{i}/{len(payload_files)}] Processing: {payload_file.name}")
        
        try:
            with open(payload_file, 'r') as f:
                raw_payload = json.load(f)
            
            # Check if payload already has webhook structure
            if 'type' in raw_payload and 'data' in raw_payload:
                payload_data = raw_payload
            else:
                # Determine webhook type
                if 'transcript' in raw_payload:
                    webhook_type = 'post_call_transcription'
                elif 'full_audio' in raw_payload:
                    webhook_type = 'post_call_audio'
                elif 'error' in raw_payload or 'error_code' in raw_payload:
                    webhook_type = 'call_initiation_failure'
                else:
                    webhook_type = 'post_call_transcription'
                payload_data = {'type': webhook_type, 'data': raw_payload}
            
            conversation_id = payload_data.get('data', {}).get('conversation_id', 'N/A')
            webhook_type = payload_data.get('type', 'N/A')
            print(f"  Conversation ID: {conversation_id}")
            print(f"  Type: {webhook_type}")
        except Exception as e:
            print(f"  ❌ Failed to read payload: {e}")
            results.append((payload_file.name, False, f"Failed to read: {e}"))
            continue
        
        success, message = await process_payload(payload_file)
        
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
        
        results.append((payload_file.name, success, message))
        print()
    
    # Print summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    successful = sum(1 for _, success, _ in results if success)
    failed = len(results) - successful
    
    print(f"Total payloads: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print()
    
    if failed > 0:
        print("Failed payloads:")
        for filename, success, message in results:
            if not success:
                print(f"  - {filename}: {message}")
        print()
    
    print("=" * 80)

if __name__ == "__main__":
    import sys
    
    # Default directory
    default_directory = "data/webhooks/+15074595005"
    
    # Get directory from command line argument or use default
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = default_directory
    
    print(f"Directory: {directory}")
    print()
    
    asyncio.run(load_all_payloads(directory))


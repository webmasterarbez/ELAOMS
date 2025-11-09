#!/usr/bin/env python3
"""Test OpenMemory API with the saved payload."""
import json
import asyncio
from config import settings
from src.clients.openmemory import OpenMemoryClient
from src.utils.helpers import extract_user_id_from_payload

async def test_openmemory():
    """Test OpenMemory API with the saved payload."""
    print("=" * 60)
    print("Testing OpenMemory API")
    print("=" * 60)
    print()
    print(f"OpenMemory URL: {settings.openmemory_url}")
    print(f"API Key configured: {'Yes' if settings.openmemory_api_key else 'No'}")
    if settings.openmemory_api_key:
        print(f"API Key length: {len(settings.openmemory_api_key)}")
    print()
    
    # Load the saved payload
    payload_path = "data/webhooks/+16129782029/conv_9901k9n0k6b2ean81hyedp2hdsn7_transcription.json"
    try:
        with open(payload_path, 'r') as f:
            payload = json.load(f)
        print(f"✓ Loaded payload from: {payload_path}")
        print(f"  Conversation ID: {payload['data']['conversation_id']}")
        print(f"  Agent ID: {payload['data']['agent_id']}")
    except FileNotFoundError:
        print(f"❌ Error: Payload file not found: {payload_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in payload file: {e}")
        return False
    
    # Extract user_id
    user_id = extract_user_id_from_payload(payload)
    if not user_id:
        user_id = payload['data']['conversation_id']
        print(f"⚠️  No user_id found, using conversation_id: {user_id}")
    else:
        print(f"✓ Extracted user_id: {user_id}")
    print()
    
    # Test OpenMemory
    openmemory = OpenMemoryClient()
    try:
        print("=" * 60)
        print("1. Testing: Store Post-Call Payload")
        print("=" * 60)
        result = await openmemory.store_post_call_payload(
            payload=payload,
            user_id=user_id
        )
        print(f"✅ SUCCESS: Stored to OpenMemory")
        print(f"   Memory ID: {result.get('id')}")
        print()
        
        print("=" * 60)
        print("2. Testing: Query Memories")
        print("=" * 60)
        memories = await openmemory.query_memories(
            query="Stefan profile information",
            user_id=user_id,
            limit=5
        )
        print(f"✅ SUCCESS: Found {len(memories)} memories")
        for i, memory in enumerate(memories, 1):
            memory_id = memory.get('id', 'N/A')
            content_preview = memory.get('content', '')[:100] + "..." if len(memory.get('content', '')) > 100 else memory.get('content', '')
            print(f"   Memory {i}: ID={memory_id}, Content={content_preview}")
        print()
        
        print("=" * 60)
        print("3. Testing: Get User Summary")
        print("=" * 60)
        summary = await openmemory.get_user_summary(user_id)
        if summary:
            print(f"✅ SUCCESS: User summary found")
            print(f"   Summary: {summary[:200]}...")
        else:
            print("⚠️  No user summary found (this is normal for new users)")
        print()
        
        await openmemory.close()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        await openmemory.close()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openmemory())
    print()
    print("=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed. Check the error messages above.")
    print("=" * 60)


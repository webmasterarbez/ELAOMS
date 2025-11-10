#!/usr/bin/env python3
"""Check webhook logs and OpenMemory storage status."""
import asyncio
import json
from pathlib import Path
from config import settings
from src.clients.openmemory import OpenMemoryClient

async def check_webhook_status():
    """Check webhook storage status."""
    print("=" * 60)
    print("Webhook Storage Status Check")
    print("=" * 60)
    print()
    
    # Check OpenMemory configuration
    print("OpenMemory Configuration:")
    print(f"  URL: {settings.openmemory_url}")
    print(f"  API Key: {'Configured' if settings.openmemory_api_key else 'NOT CONFIGURED'}")
    print()
    
    # Check saved webhook files
    webhook_dir = Path("data/webhooks")
    if webhook_dir.exists():
        print("Saved Webhook Files:")
        files = list(webhook_dir.rglob("*.json"))
        print(f"  Found {len(files)} webhook files")
        for file in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
            print(f"  - {file} (modified: {file.stat().st_mtime})")
    else:
        print("  No webhook files found")
    print()
    
    # Check OpenMemory storage
    print("OpenMemory Storage Check:")
    client = OpenMemoryClient()
    try:
        # Check for user +16129782029
        user_id = "+16129782029"
        print(f"  Checking memories for user: {user_id}")
        
        # Query memories
        memories = await client.query_memories(
            query="conversation transcript",
            user_id=user_id,
            limit=10
        )
        print(f"  Query results: {len(memories)} memories found")
        
        # Get user summary
        summary = await client.get_user_summary(user_id)
        if summary:
            print(f"  User summary: {summary[:150]}...")
        else:
            print("  No user summary found")
        
        # Try to get all memories by querying with empty query
        all_memories = await client.query_memories(
            query="",
            user_id=user_id,
            limit=100
        )
        print(f"  All memories (empty query): {len(all_memories)} found")
        
        if all_memories:
            print("  Memory IDs:")
            for mem in all_memories[:5]:
                mem_id = mem.get('id', 'N/A')
                content_preview = mem.get('content', '')[:50] + "..." if len(mem.get('content', '')) > 50 else mem.get('content', '')
                print(f"    - {mem_id}: {content_preview}")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(check_webhook_status())



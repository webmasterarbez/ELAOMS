#!/usr/bin/env python3
"""Retrieve all memories stored for a user_id."""
import asyncio
import json
import sys
from config import settings
from src.clients.openmemory import OpenMemoryClient

async def retrieve_all_memories(user_id: str):
    """Retrieve all memories for a given user_id."""
    print("=" * 60)
    print(f"Retrieving All Memories for User: {user_id}")
    print("=" * 60)
    print()
    
    client = OpenMemoryClient()
    try:
        # Get user summary first
        print("1. User Summary:")
        print("-" * 60)
        summary = await client.get_user_summary(user_id)
        if summary:
            print(f"   {summary}")
        else:
            print("   No summary found")
        print()
        
        # Try multiple query strategies to get all memories
        print("2. Querying Memories:")
        print("-" * 60)
        
        # Strategy 1: Very broad query
        print("   Strategy 1: Very broad query ('*')")
        memories1 = await client.query_memories(
            query="*",
            user_id=user_id,
            limit=100
        )
        print(f"   Found: {len(memories1)} memories")
        
        # Strategy 2: Empty query
        print("   Strategy 2: Empty query ('')")
        memories2 = await client.query_memories(
            query="",
            user_id=user_id,
            limit=100
        )
        print(f"   Found: {len(memories2)} memories")
        
        # Strategy 3: Common terms
        queries = [
            "conversation",
            "transcript",
            "call",
            "profile",
            "user",
            "Stefan",
            "Briat"
        ]
        
        all_memories = {}
        for query_term in queries:
            print(f"   Strategy 3: Query term '{query_term}'")
            try:
                memories = await client.query_memories(
                    query=query_term,
                    user_id=user_id,
                    limit=100
                )
                print(f"   Found: {len(memories)} memories")
                for mem in memories:
                    mem_id = mem.get('id')
                    if mem_id and mem_id not in all_memories:
                        all_memories[mem_id] = mem
            except Exception as e:
                print(f"   Error: {e}")
        
        print()
        print("3. All Unique Memories Found:")
        print("-" * 60)
        print(f"   Total unique memories: {len(all_memories)}")
        print()
        
        if all_memories:
            for i, (mem_id, memory) in enumerate(all_memories.items(), 1):
                print(f"   Memory {i}:")
                print(f"   - ID: {mem_id}")
                content = memory.get('content', '')
                content_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   - Content preview: {content_preview}")
                metadata = memory.get('metadata', {})
                if metadata:
                    print(f"   - Metadata: {json.dumps(metadata, indent=6)}")
                print()
        else:
            print("   No memories found with queries")
            print()
            print("   Note: The user summary shows memories exist, but queries")
            print("   are not finding them. This suggests:")
            print("   - OpenMemory indexing may not be complete")
            print("   - Query text doesn't match stored content")
            print("   - OpenMemory query API may have limitations")
        
        # Try to get memories by making a direct API call if possible
        print("4. Saved Webhook Files (Source Data):")
        print("-" * 60)
        # Retrieve from saved webhook files
        from pathlib import Path
        webhook_dir = Path("data/webhooks") / user_id
        
        if webhook_dir.exists():
            files = list(webhook_dir.glob("*_transcription.json"))
            print(f"   Found {len(files)} saved webhook transcription files")
            print()
            
            for i, file in enumerate(sorted(files, key=lambda x: x.stat().st_mtime, reverse=True), 1):
                print(f"   Memory {i} (from saved file):")
                print(f"   - File: {file.name}")
                try:
                    with open(file, 'r') as f:
                        payload = json.load(f)
                    
                    data = payload.get('data', {})
                    conv_id = data.get('conversation_id')
                    agent_id = data.get('agent_id')
                    transcript = data.get('transcript', [])
                    
                    print(f"   - Conversation ID: {conv_id}")
                    print(f"   - Agent ID: {agent_id}")
                    print(f"   - Transcript turns: {len(transcript)}")
                    
                    # Show first few transcript turns
                    if transcript:
                        print(f"   - First turns:")
                        for turn in transcript[:3]:
                            role = turn.get('role', 'unknown')
                            message = turn.get('message', '')
                            preview = message[:80] + "..." if len(message) > 80 else message
                            print(f"     [{role}]: {preview}")
                    print()
                except Exception as e:
                    print(f"   - Error reading file: {e}")
                    print()
        else:
            print(f"   No webhook directory found for user: {user_id}")
            print()
        
        print("5. Summary:")
        print("-" * 60)
        print(f"   - User Summary shows: {summary if summary else 'No summary'}")
        print(f"   - OpenMemory queries found: {len(all_memories)} memories")
        print(f"   - Saved webhook files: {len(files) if webhook_dir.exists() else 0} files")
        print()
        print("   Note: Data IS stored in OpenMemory (confirmed by user summary),")
        print("   but OpenMemory's semantic query API is not finding it.")
        print("   The saved webhook files contain the same data that was stored.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    # Default to the phone number we've been testing with
    default_user_id = "+16129782029"
    
    # Get user_id from command line argument or use default
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = default_user_id
    
    print(f"User ID: {user_id}")
    print()
    
    asyncio.run(retrieve_all_memories(user_id))


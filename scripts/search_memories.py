#!/usr/bin/env python3
"""Search OpenMemory for all memories using a phone number/user_id."""
import asyncio
import json
import sys
import httpx
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings

async def get_all_memories_direct(user_id: str) -> List[Dict[str, Any]]:
    """Get all memories for a user using the direct API endpoint."""
    base_url = settings.openmemory_url.rstrip("/")
    
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "X-API-Key": settings.openmemory_api_key,
            "Content-Type": "application/json"
        },
        timeout=30.0
    ) as client:
        try:
            # Try the /users/{user_id}/memories endpoint
            response = await client.get(f"/users/{user_id}/memories")
            if response.status_code == 200:
                result = response.json()
                # Handle different response formats
                if "items" in result:
                    return result["items"]
                elif "memories" in result:
                    return result["memories"]
                elif isinstance(result, list):
                    return result
                else:
                    return []
            else:
                print(f"  API returned status {response.status_code}: {response.text[:200]}")
                return []
        except httpx.HTTPStatusError as e:
            print(f"  HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return []
        except Exception as e:
            print(f"  Error: {e}")
            return []

async def query_memories_multiple_strategies(user_id: str) -> List[Dict[str, Any]]:
    """Query memories using multiple query strategies."""
    base_url = settings.openmemory_url.rstrip("/")
    all_memories = {}
    
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={
            "X-API-Key": settings.openmemory_api_key,
            "Content-Type": "application/json"
        },
        timeout=30.0
    ) as client:
        # Try multiple query strategies
        queries = [
            "",  # Empty query
            "*",  # Wildcard
            "conversation",
            "transcript",
            "call",
            "post_call",
        ]
        
        for query in queries:
            try:
                payload = {
                    "query": query if query else " ",
                    "user_id": user_id,
                    "limit": 100
                }
                response = await client.post("/memory/query", json=payload)
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    if isinstance(memories, list):
                        for mem in memories:
                            mem_id = mem.get("id") or mem.get("memory_id")
                            if mem_id and mem_id not in all_memories:
                                all_memories[mem_id] = mem
            except Exception as e:
                continue
    
    return list(all_memories.values())

async def search_memories(user_id: str):
    """Search OpenMemory for all memories for a given user_id."""
    print("=" * 80)
    print(f"Searching OpenMemory for Memories")
    print(f"User ID: {user_id}")
    print("=" * 80)
    print()
    
    # Strategy 1: Direct API call to get all memories
    print("Strategy 1: Direct API call (/users/{user_id}/memories)")
    print("-" * 80)
    memories_direct = await get_all_memories_direct(user_id)
    print(f"Found {len(memories_direct)} memories via direct API")
    print()
    
    # Strategy 2: Query with multiple strategies
    print("Strategy 2: Query API with multiple query terms")
    print("-" * 80)
    memories_query = await query_memories_multiple_strategies(user_id)
    print(f"Found {len(memories_query)} unique memories via query API")
    print()
    
    # Combine results (deduplicate by ID)
    all_memories = {}
    for mem in memories_direct + memories_query:
        mem_id = mem.get("id") or mem.get("memory_id")
        if mem_id:
            all_memories[mem_id] = mem
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total unique memories found: {len(all_memories)}")
    print()
    
    if all_memories:
        print("=" * 80)
        print("MEMORY DETAILS")
        print("=" * 80)
        
        for i, (mem_id, memory) in enumerate(sorted(all_memories.items()), 1):
            print(f"\n[{i}] Memory ID: {mem_id}")
            
            # Debug: show all keys in memory
            print(f"    Memory Keys: {list(memory.keys())}")
            
            # Extract metadata
            metadata = memory.get("metadata", {})
            if metadata:
                print(f"    Metadata: {json.dumps(metadata, indent=8)}")
                conv_id = metadata.get("conversation_id")
                agent_id = metadata.get("agent_id")
                event_type = metadata.get("event_type")
                
                if conv_id:
                    print(f"    Conversation ID: {conv_id}")
                if agent_id:
                    print(f"    Agent ID: {agent_id}")
                if event_type:
                    print(f"    Event Type: {event_type}")
            else:
                print(f"    Metadata: (empty)")
            
            # Try to parse content as JSON to extract more details
            # Check multiple possible content fields
            content = memory.get("content") or memory.get("text") or memory.get("data") or ""
            
            # Show content info
            if content:
                if isinstance(content, str):
                    print(f"    Content Length: {len(content)} characters")
                    if len(content) > 0:
                        print(f"    Content Preview (first 200 chars): {content[:200]}...")
                else:
                    print(f"    Content Type: {type(content)}")
            
            if content:
                try:
                    # Try to parse as JSON
                    if isinstance(content, str) and (content.startswith("{") or content.startswith("[")):
                        content_json = json.loads(content)
                    elif isinstance(content, dict):
                        content_json = content
                    else:
                        content_json = None
                    
                    if content_json and isinstance(content_json, dict):
                        # Check if it's a webhook payload
                        if "type" in content_json and "data" in content_json:
                            data = content_json.get("data", {})
                            conv_id = data.get("conversation_id")
                            agent_id = data.get("agent_id")
                            status = data.get("status")
                            transcript = data.get("transcript", [])
                            
                            print(f"    Type: {content_json.get('type')}")
                            if conv_id:
                                print(f"    Conversation ID: {conv_id}")
                            if agent_id:
                                print(f"    Agent ID: {agent_id}")
                            if status:
                                print(f"    Status: {status}")
                            if transcript:
                                print(f"    Transcript Turns: {len(transcript)}")
                                
                                # Show first few turns
                                if transcript:
                                    print(f"    First Turn:")
                                    first_turn = transcript[0]
                                    role = first_turn.get("role", "unknown")
                                    message = first_turn.get("message", "")
                                    preview = message[:100] + "..." if len(message) > 100 else message
                                    print(f"      [{role}]: {preview}")
                        else:
                            # Not a webhook payload, show keys
                            print(f"    Content Keys: {list(content_json.keys())[:10]}")
                except json.JSONDecodeError:
                    # Not JSON, show content preview
                    if isinstance(content, str):
                        preview = content[:150] + "..." if len(content) > 150 else content
                        print(f"    Content Preview: {preview}")
                except Exception as e:
                    print(f"    Error parsing content: {e}")
            
            # Show timestamps
            created_at = memory.get("created_at")
            updated_at = memory.get("updated_at")
            if created_at:
                try:
                    if isinstance(created_at, (int, float)):
                        dt = datetime.fromtimestamp(created_at / 1000 if created_at > 1e10 else created_at)
                        print(f"    Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception:
                    pass
            if updated_at:
                try:
                    if isinstance(updated_at, (int, float)):
                        dt = datetime.fromtimestamp(updated_at / 1000 if updated_at > 1e10 else updated_at)
                        print(f"    Updated: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception:
                    pass
            
            print()
    else:
        print("No memories found in OpenMemory.")
        print()
        print("Note: This could mean:")
        print("  - No memories have been stored for this user_id")
        print("  - The user_id format doesn't match what was stored")
        print("  - OpenMemory indexing is not complete")
        print()
    
    # Also check for saved webhook files
    print("=" * 80)
    print("SAVED WEBHOOK FILES")
    print("=" * 80)
    webhook_dir = Path("data/webhooks") / user_id
    
    if webhook_dir.exists():
        payload_files = list(webhook_dir.glob("*_payload.json"))
        transcription_files = list(webhook_dir.glob("*_transcription.json"))
        
        print(f"Found {len(payload_files)} payload files")
        print(f"Found {len(transcription_files)} transcription files")
        print()
        
        if payload_files or transcription_files:
            print("Files:")
            for file in sorted(payload_files + transcription_files, key=lambda x: x.stat().st_mtime, reverse=True):
                print(f"  - {file.name}")
    else:
        print(f"No webhook directory found for user: {user_id}")
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    # Default to the phone number requested
    default_user_id = "+15074595005"
    
    # Get user_id from command line argument or use default
    if len(sys.argv) > 1:
        user_id = sys.argv[1]
    else:
        user_id = default_user_id
    
    print(f"Searching for memories with user_id: {user_id}")
    print()
    
    asyncio.run(search_memories(user_id))


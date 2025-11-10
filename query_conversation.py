#!/usr/bin/env python3
"""Query OpenMemory for a specific conversation."""
import asyncio
import json
import httpx
from src.clients.openmemory import OpenMemoryClient
from config import settings

async def query_conversation_in_openmemory():
    """Query OpenMemory for the specific conversation."""
    user_id = "+16129782029"
    conversation_id = "conv_7401k9nt84z5enn8q0b6xs9jvzs0"
    
    print("=" * 80)
    print(f"Querying OpenMemory for Conversation: {conversation_id}")
    print(f"User ID: {user_id}")
    print("=" * 80)
    print()
    
    client = OpenMemoryClient()
    try:
        # Query with conversation_id filter
        print("Querying with conversation_id filter...")
        memories = await client.query_memories(
            query="conversation",
            user_id=user_id,
            limit=10,
            filters={"conversation_id": conversation_id}
        )
        
        print(f"Found {len(memories)} memory/memories")
        print()
        
        if memories:
            for i, memory in enumerate(memories, 1):
                print(f"Memory {i}:")
                print("-" * 80)
                print(f"  Memory ID: {memory.get('id')}")
                
                # Show metadata
                metadata = memory.get('metadata', {})
                if metadata:
                    print(f"  Metadata:")
                    print(f"    - conversation_id: {metadata.get('conversation_id')}")
                    print(f"    - agent_id: {metadata.get('agent_id')}")
                    print(f"    - event_type: {metadata.get('event_type')}")
                    print(f"    - event_timestamp: {metadata.get('event_timestamp')}")
                
                # Show content preview
                content = memory.get('content', '')
                print(f"  Content length: {len(content)} characters")
                
                # Try to parse as JSON to show structure
                try:
                    content_json = json.loads(content)
                    print(f"  Content is valid JSON")
                    print(f"  Top-level keys: {list(content_json.keys())}")
                    
                    # Show data section keys
                    if 'data' in content_json:
                        data_keys = list(content_json['data'].keys())
                        print(f"  Data keys: {data_keys[:10]}...")  # First 10 keys
                    
                    # Show preview of content
                    content_preview = json.dumps(content_json, indent=2)[:500]
                    print(f"  Content preview (first 500 chars):")
                    print(f"  {content_preview}...")
                except json.JSONDecodeError:
                    # Not JSON, show as text
                    content_preview = content[:500]
                    print(f"  Content preview (first 500 chars):")
                    print(f"  {content_preview}...")
                
                print()
        else:
            print("No memories found with conversation_id filter.")
            print()
            print("Trying alternative query strategies...")
            
            # Try various query terms
            query_terms = [
                conversation_id,
                "transcript",
                "conversation",
                "post_call",
                "Stefan",
                "call",
                "",
                "*"
            ]
            
            all_found_memories = {}
            for query_term in query_terms:
                try:
                    found = await client.query_memories(
                        query=query_term,
                        user_id=user_id,
                        limit=100
                    )
                    print(f"Query '{query_term}': Found {len(found)} memories")
                    for mem in found:
                        mem_id = mem.get('id')
                        if mem_id and mem_id not in all_found_memories:
                            all_found_memories[mem_id] = mem
                except Exception as e:
                    print(f"Query '{query_term}': Error - {e}")
            
            if all_found_memories:
                print(f"\nTotal unique memories found: {len(all_found_memories)}")
                print("\nAll memories for this user:")
                for mem_id, mem in all_found_memories.items():
                    mem_metadata = mem.get('metadata', {})
                    mem_conv_id = mem_metadata.get('conversation_id')
                    print(f"  - Memory ID: {mem_id}")
                    print(f"    conversation_id: {mem_conv_id}")
                    print(f"    agent_id: {mem_metadata.get('agent_id')}")
                    print(f"    event_type: {mem_metadata.get('event_type')}")
                    
                    # Check if this is our target conversation
                    if mem_conv_id == conversation_id:
                        print(f"    *** THIS IS THE TARGET CONVERSATION ***")
                        content = mem.get('content', '')
                        print(f"    Content length: {len(content)} characters")
                        try:
                            content_json = json.loads(content)
                            print(f"    Content is valid JSON")
                            print(f"    Top-level keys: {list(content_json.keys())}")
                        except:
                            pass
                    print()
        
        # Also get user summary
        print()
        print("User Summary:")
        print("-" * 80)
        summary = await client.get_user_summary(user_id)
        if summary:
            print(f"  {summary}")
        else:
            print("  No summary found")
        
        # Try direct API call to see if there's a list endpoint
        print()
        print("Trying direct API calls...")
        print("-" * 80)
        try:
            # Try to get all memories directly (if such endpoint exists)
            base_url = settings.openmemory_url.rstrip("/")
            async with httpx.AsyncClient(
                base_url=base_url,
                headers={
                    "X-API-Key": settings.openmemory_api_key,
                    "Content-Type": "application/json"
                },
                timeout=30.0
            ) as direct_client:
                # Try /users/{user_id}/memories endpoint
                try:
                    response = await direct_client.get(f"/users/{user_id}/memories")
                    if response.status_code == 200:
                        result = response.json()
                        memories_list = result.get("memories", [])
                        print(f"Direct GET /users/{user_id}/memories: Found {len(memories_list)} memories")
                        if memories_list:
                            for mem in memories_list:
                                mem_metadata = mem.get('metadata', {})
                                mem_conv_id = mem_metadata.get('conversation_id')
                                if mem_conv_id == conversation_id:
                                    print(f"  *** FOUND TARGET CONVERSATION ***")
                                    print(f"  Memory ID: {mem.get('id')}")
                                    print(f"  Metadata: {json.dumps(mem_metadata, indent=4)}")
                                    content = mem.get('content', '')
                                    print(f"  Content length: {len(content)} characters")
                                    try:
                                        content_json = json.loads(content)
                                        print(f"  Content is valid JSON")
                                        print(f"  Top-level keys: {list(content_json.keys())}")
                                    except:
                                        pass
                except httpx.HTTPStatusError as e:
                    if e.response.status_code != 404:
                        print(f"  GET /users/{user_id}/memories: {e.response.status_code}")
                except Exception as e:
                    print(f"  GET /users/{user_id}/memories: Error - {e}")
                
                # Try query with space instead of empty string
                try:
                    payload = {
                        "query": " ",
                        "user_id": user_id,
                        "limit": 100
                    }
                    response = await direct_client.post("/memory/query", json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        memories_space = result.get("memories", [])
                        print(f"Query with space (' '): Found {len(memories_space)} memories")
                        if memories_space:
                            for mem in memories_space:
                                mem_metadata = mem.get('metadata', {})
                                mem_conv_id = mem_metadata.get('conversation_id')
                                if mem_conv_id == conversation_id:
                                    print(f"  *** FOUND TARGET CONVERSATION ***")
                                    print(f"  Memory ID: {mem.get('id')}")
                                    print(f"  Metadata: {json.dumps(mem_metadata, indent=4)}")
                except Exception as e:
                    print(f"  Query with space: Error - {e}")
        except Exception as e:
            print(f"  Direct API call error: {e}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()
    
    print()
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(query_conversation_in_openmemory())


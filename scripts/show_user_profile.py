"""Script to display a user profile from OpenMemory."""
import asyncio
import httpx
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

async def get_user_summary(client: httpx.AsyncClient, user_id: str) -> str:
    """Get user summary from OpenMemory."""
    try:
        response = await client.get(f"/users/{user_id}/summary")
        if response.status_code == 200:
            data = response.json()
            return data.get("summary", "No summary available")
    except Exception:
        pass
    return "No summary available"

async def get_all_memories(client: httpx.AsyncClient, user_id: str) -> List[Dict[str, Any]]:
    """Get all memories for a user using multiple query strategies."""
    all_memories = []
    seen_ids = set()
    
    queries = ["", "conversation", "transcript", "call", "memory"]
    
    for query in queries:
        try:
            payload = {
                "query": query if query else " ",
                "user_id": user_id,
                "limit": 50
            }
            response = await client.post("/memory/query", json=payload)
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                if isinstance(memories, list):
                    for mem in memories:
                        mem_id = mem.get("id") or mem.get("memory_id")
                        if mem_id and mem_id not in seen_ids:
                            seen_ids.add(mem_id)
                            all_memories.append(mem)
        except Exception:
            continue
    
    return all_memories

async def show_user_profile(user_id: str):
    """Display user profile from OpenMemory."""
    openmemory_url = os.getenv("OPENMEMORY_URL", "http://localhost:8080")
    openmemory_api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    if not openmemory_api_key:
        print("⚠ Warning: OPENMEMORY_API_KEY not set")
        return
    
    async with httpx.AsyncClient(
        base_url=openmemory_url,
        headers={"X-API-Key": openmemory_api_key},
        timeout=30.0
    ) as client:
        print("=" * 80)
        print("USER PROFILE")
        print("=" * 80)
        print(f"User ID: {user_id}")
        print()
        
        # Get summary
        print("Fetching user summary...")
        summary = await get_user_summary(client, user_id)
        print(f"Summary: {summary}")
        print()
        
        # Get memories
        print("Fetching memories...")
        memories = await get_all_memories(client, user_id)
        print(f"Total Memories: {len(memories)}")
        print()
        
        # Analyze memories
        memory_types = {}
        conversation_memories = []
        
        for mem in memories:
            mem_type = mem.get("type", "unknown")
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            content = str(mem.get("content", ""))
            if "post_call_transcription" in content.lower() or "conversation_id" in content.lower():
                conversation_memories.append(mem)
        
        print("=" * 80)
        print("PROFILE STATISTICS")
        print("=" * 80)
        print(f"Total Memories: {len(memories)}")
        print(f"Conversation Memories: {len(conversation_memories)}")
        print(f"Memory Types: {dict(memory_types)}")
        print()
        
        # Show conversation details
        if conversation_memories:
            print("=" * 80)
            print("CONVERSATION MEMORIES")
            print("=" * 80)
            
            for i, mem in enumerate(conversation_memories[:10], 1):
                print(f"\n[{i}] Memory ID: {mem.get('id', mem.get('memory_id', 'N/A'))}")
                print(f"    Type: {mem.get('type', 'N/A')}")
                
                content = str(mem.get("content", ""))
                try:
                    # Try to parse as JSON to extract conversation details
                    if content.startswith("{") or content.startswith("["):
                        data = json.loads(content)
                        if isinstance(data, dict):
                            if "data" in data:
                                conv_data = data["data"]
                                conv_id = conv_data.get("conversation_id", "N/A")
                                agent_id = conv_data.get("agent_id", "N/A")
                                status = conv_data.get("status", "N/A")
                                transcript = conv_data.get("transcript", [])
                                analysis = conv_data.get("analysis", {})
                                
                                print(f"    Conversation ID: {conv_id}")
                                print(f"    Agent ID: {agent_id}")
                                print(f"    Status: {status}")
                                print(f"    Transcript Turns: {len(transcript)}")
                                if analysis:
                                    call_successful = analysis.get("call_successful", "N/A")
                                    summary = analysis.get("transcript_summary", "")
                                    print(f"    Call Successful: {call_successful}")
                                    if summary:
                                        print(f"    Summary: {summary[:150]}...")
                except json.JSONDecodeError:
                    # Not JSON, show content preview
                    if len(content) > 200:
                        content = content[:200] + "..."
                    print(f"    Content: {content[:100]}...")
                
                # Show timestamp if available
                timestamp = mem.get("timestamp") or mem.get("created_at")
                if timestamp:
                    try:
                        if isinstance(timestamp, (int, float)):
                            dt = datetime.fromtimestamp(timestamp / 1000 if timestamp > 1e10 else timestamp)
                            print(f"    Timestamp: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    except Exception:
                        pass
        
        print()
        print("=" * 80)

if __name__ == "__main__":
    user_id = sys.argv[1] if len(sys.argv) > 1 else "+15074595005"
    print(f"\nDisplaying profile for: {user_id}")
    print("Make sure OpenMemory is running and OPENMEMORY_API_KEY is set\n")
    asyncio.run(show_user_profile(user_id))


"""Script to store multiple Eleven Labs conversations to OpenMemory."""
import asyncio
import httpx
import json
import os
import time
from typing import List, Dict, Any

async def store_conversation(
    conversation_id: str,
    elevenlabs_key: str,
    user_id: str,
    openmemory_url: str,
    openmemory_api_key: str
) -> Dict[str, Any]:
    """Store a single conversation to OpenMemory."""
    print(f"\n📞 Processing conversation: {conversation_id}")
    
    # Fetch conversation from Eleven Labs
    elevenlabs_url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    
    try:
        async with httpx.AsyncClient() as el_client:
            response = await el_client.get(
                elevenlabs_url,
                headers={"xi-api-key": elevenlabs_key},
                timeout=30.0
            )
            response.raise_for_status()
            conversation_data = response.json()
        
        print(f"   ✓ Fetched conversation: {conversation_data.get('conversation_id', 'unknown')}")
        print(f"   Status: {conversation_data.get('status', 'unknown')}")
        
        # Extract user_id from conversation (prioritizes system__caller_id for consistent caller identification)
        actual_user_id = user_id
        init_data = conversation_data.get("conversation_initiation_client_data", {})
        dynamic_vars = init_data.get("dynamic_variables", {})
        
        # Priority 1: system__caller_id (most consistent for same caller)
        caller_id = dynamic_vars.get("system__caller_id")
        if caller_id:
            actual_user_id = str(caller_id)
            print(f"   Using system__caller_id: {actual_user_id}")
        # Priority 2: user_id from conversation_initiation_client_data
        elif init_data.get("user_id"):
            actual_user_id = str(init_data.get("user_id"))
            print(f"   Using conversation_initiation_client_data.user_id: {actual_user_id}")
        # Priority 3: user_id from metadata
        elif conversation_data.get("metadata", {}).get("user_id"):
            actual_user_id = str(conversation_data.get("metadata", {}).get("user_id"))
            print(f"   Using metadata.user_id: {actual_user_id}")
        # Priority 4: user_id from dynamic_variables
        elif dynamic_vars.get("user_id"):
            actual_user_id = str(dynamic_vars.get("user_id"))
            print(f"   Using dynamic_variables.user_id: {actual_user_id}")
        # Fallback: use provided user_id or conversation_id
        else:
            actual_user_id = user_id or conversation_data.get("conversation_id", "unknown")
            print(f"   Using fallback user_id: {actual_user_id}")
        
        # Get metadata for timestamp
        metadata = conversation_data.get("metadata", {})
        
        # Create webhook payload
        webhook_payload = {
            "type": "post_call_transcription",
            "data": conversation_data,
            "event_timestamp": metadata.get("start_time_unix_secs") or int(time.time()),
            "_stored_at": int(time.time() * 1000)
        }
        
        # Store to OpenMemory with correct format
        content = json.dumps(webhook_payload, indent=2)
        metadata_filters = {
            "conversation_id": conversation_data.get("conversation_id"),
            "agent_id": conversation_data.get("agent_id"),
            "event_type": "post_call_transcription"
        }
        
        store_payload = {
            "content": content,
            "user_id": actual_user_id,
            "filters": metadata_filters
        }
        
        # Store to OpenMemory
        async with httpx.AsyncClient(
            base_url=openmemory_url,
            headers={
                "X-API-Key": openmemory_api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        ) as om_client:
            response = await om_client.post("/memory/add", json=store_payload)
            response.raise_for_status()
            result = response.json()
            memory_id = result.get("id")
        
        print(f"   ✓ Stored to OpenMemory")
        print(f"   Memory ID: {memory_id}")
        
        # Get conversation stats
        transcript = conversation_data.get("transcript", [])
        analysis = conversation_data.get("analysis", {})
        print(f"   Transcript turns: {len(transcript)}")
        if analysis:
            print(f"   Call successful: {analysis.get('call_successful', False)}")
            if analysis.get("transcript_summary"):
                print(f"   Summary: {analysis.get('transcript_summary')[:100]}...")
        
        return {
            "conversation_id": conversation_data.get("conversation_id"),
            "memory_id": memory_id,
            "user_id": actual_user_id,
            "status": "success",
            "transcript_turns": len(transcript),
            "call_successful": analysis.get("call_successful", False) if analysis else None
        }
        
    except httpx.HTTPStatusError as e:
        print(f"   ✗ Error fetching conversation: {e.response.status_code}")
        if e.response.status_code == 404:
            print(f"   Conversation not found")
        return {
            "conversation_id": conversation_id,
            "status": "error",
            "error": f"HTTP {e.response.status_code}"
        }
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return {
            "conversation_id": conversation_id,
            "status": "error",
            "error": str(e)
        }


async def store_all_conversations(
    conversation_ids: List[str],
    user_id: str = None
) -> Dict[str, Any]:
    """Store all conversations to OpenMemory."""
    openmemory_url = os.getenv("OPENMEMORY_URL", "http://localhost:8080")
    openmemory_api_key = os.getenv("OPENMEMORY_API_KEY", "")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    
    if not openmemory_api_key:
        print("⚠ Warning: OPENMEMORY_API_KEY not set")
        return
    
    if not elevenlabs_key:
        print("⚠ Error: ELEVENLABS_API_KEY not set")
        return
    
    print("=" * 80)
    print("Storing Eleven Labs Conversations to OpenMemory")
    print("=" * 80)
    print(f"OpenMemory URL: {openmemory_url}")
    print(f"Conversations to store: {len(conversation_ids)}")
    print()
    
    results = []
    successful = 0
    failed = 0
    
    for i, conv_id in enumerate(conversation_ids, 1):
        print(f"\n[{i}/{len(conversation_ids)}] Processing conversation...")
        
        # Use conversation_id as user_id if not provided
        default_user_id = user_id or f"user_{conv_id[:15]}"
        
        result = await store_conversation(
            conv_id,
            elevenlabs_key,
            default_user_id,
            openmemory_url,
            openmemory_api_key
        )
        
        results.append(result)
        
        if result.get("status") == "success":
            successful += 1
        else:
            failed += 1
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("Storage Summary")
    print("=" * 80)
    print(f"Total conversations: {len(conversation_ids)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print()
    
    print("Results:")
    for result in results:
        if result.get("status") == "success":
            print(f"  ✓ {result.get('conversation_id')} -> Memory ID: {result.get('memory_id')}")
            print(f"    User ID: {result.get('user_id')}, Turns: {result.get('transcript_turns')}")
        else:
            print(f"  ✗ {result.get('conversation_id')}: {result.get('error', 'Unknown error')}")
    
    # Save results to file
    output_file = "data/conversation_storage_results.json"
    os.makedirs("data", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print("=" * 80)
    
    return {
        "total": len(conversation_ids),
        "successful": successful,
        "failed": failed,
        "results": results
    }


if __name__ == "__main__":
    # Conversation IDs to store
    conversation_ids = [
        "conv_01jxd5y165f62a0v7gtr6bkg56",
        "conv_01jxk1wejhenk8x8tt9enzxw4a",
        "conv_01jy1xxqmje7arqq7m1pqrfmav",
        "conv_01jy1zdbj8emq934gk1kby2pqh",
        "conv_01jyqd6gkmed4ty6xfjpwrf20c"
    ]
    
    print("\nStoring conversations to OpenMemory...")
    print("Make sure OpenMemory is running and OPENMEMORY_API_KEY is set\n")
    
    asyncio.run(store_all_conversations(conversation_ids))


"""Standalone test script to verify OpenMemory handles full post-call webhook payloads correctly."""
import asyncio
import httpx
import json
import logging
import os
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleOpenMemoryClient:
    """Simple OpenMemory client for testing."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def store_memory(
        self,
        content: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a memory in OpenMemory."""
        payload = {
            "content": content,
            "user_id": user_id,
            "filters": metadata or {}
        }
        
        response = await self.client.post("/memory/add", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def query_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> list:
        """Query memories from OpenMemory."""
        payload = {
            "query": query,
            "limit": limit,
            "user_id": user_id,
            "filters": filters or {}
        }
        
        response = await self.client.post("/memory/query", json=payload)
        response.raise_for_status()
        result = response.json()
        return result.get("memories", [])
    
    async def get_user_summary(self, user_id: str) -> Optional[str]:
        """Get user summary from OpenMemory."""
        try:
            response = await self.client.get(f"/users/{user_id}/summary")
            response.raise_for_status()
            result = response.json()
            return result.get("summary")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def store_post_call_payload(
        self,
        payload: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Store entire post-call webhook payload to OpenMemory."""
        # Convert entire payload to JSON string for storage
        content = json.dumps(payload, indent=2)
        
        metadata = {
            "conversation_id": payload.get("data", {}).get("conversation_id"),
            "agent_id": payload.get("data", {}).get("agent_id"),
            "event_type": payload.get("type"),
            "event_timestamp": payload.get("event_timestamp")
        }
        
        return await self.store_memory(
            content=content,
            user_id=user_id,
            metadata=metadata
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def test_post_call_storage():
    """Test storing a conversation from Eleven Labs API to OpenMemory."""
    
    # Configuration from environment or defaults
    openmemory_url = os.getenv("OPENMEMORY_URL", "http://localhost:8080")
    openmemory_api_key = os.getenv("OPENMEMORY_API_KEY", "")
    
    if not openmemory_api_key:
        print("⚠ Warning: OPENMEMORY_API_KEY not set. Using empty key (may fail)")
    
    # Step 1: Fetch conversation from Eleven Labs
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    
    if not elevenlabs_key:
        print("⚠ Error: ELEVENLABS_API_KEY not set")
        return
    
    # Example conversation ID - replace with actual conversation ID for testing
    conversation_id = os.getenv("TEST_CONVERSATION_ID", "conv_01jxd5y165f62a0v7gtr6bkg56")
    elevenlabs_url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
    
    print("=" * 80)
    print("Testing Post-Call Webhook Storage with OpenMemory")
    print("=" * 80)
    print("\nStep 1: Fetching conversation from Eleven Labs...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                elevenlabs_url,
                headers={"xi-api-key": elevenlabs_key},
                timeout=30.0
            )
            response.raise_for_status()
            conversation_data = response.json()
        
        conversation_id = conversation_data.get("conversation_id", "unknown")
        print(f"✓ Fetched conversation: {conversation_id}")
        print(f"  Status: {conversation_data.get('status', 'unknown')}")
        print(f"  Agent ID: {conversation_data.get('agent_id', 'unknown')}")
        
        # Check transcript length
        transcript = conversation_data.get("transcript", [])
        print(f"  Transcript turns: {len(transcript)}")
        
        # Check analysis
        analysis = conversation_data.get("analysis", {})
        if analysis:
            print(f"  Has analysis: Yes")
            print(f"  Call successful: {analysis.get('call_successful', 'unknown')}")
            if analysis.get("transcript_summary"):
                print(f"  Summary length: {len(analysis.get('transcript_summary', ''))} chars")
        
    except Exception as e:
        print(f"✗ Error fetching conversation: {e}")
        logger.error(f"Error fetching conversation: {e}", exc_info=True)
        return
    
    # Step 2: Transform to post-call webhook format
    webhook_payload = {
        "type": "post_call_transcription",
        "data": conversation_data,
        "event_timestamp": conversation_data.get("metadata", {}).get("start_time_unix_secs")
    }
    
    # Step 3: Extract user_id
    user_id = conversation_data.get("metadata", {}).get("user_id")
    if not user_id:
        init_data = conversation_data.get("conversation_initiation_client_data", {})
        user_id = init_data.get("user_id")
        if not user_id:
            dynamic_vars = init_data.get("dynamic_variables", {})
            user_id = dynamic_vars.get("user_id") or dynamic_vars.get("caller_id")
            if not user_id:
                user_id = f"test_user_{conversation_id[:10]}"
    
    print(f"\n✓ Using user_id: {user_id}")
    
    # Step 4: Store to OpenMemory using our current method
    print("\nStep 2: Storing to OpenMemory using current approach...")
    print(f"  OpenMemory URL: {openmemory_url}")
    
    openmemory = SimpleOpenMemoryClient(openmemory_url, openmemory_api_key)
    try:
        # Check OpenMemory connection first
        try:
            health_response = await openmemory.client.get("/health")
            print(f"  OpenMemory health: {health_response.status_code}")
        except Exception as e:
            print(f"  Warning: Could not check OpenMemory health: {e}")
        
        result = await openmemory.store_post_call_payload(
            payload=webhook_payload,
            user_id=user_id
        )
        memory_id = result.get("id")
        print(f"✓ Stored successfully! Memory ID: {memory_id}")
        
        # Step 5: Query it back to see how OpenMemory processed it
        print("\nStep 3: Querying back from OpenMemory...")
        print("  Testing semantic search capabilities...")
        
        # Try different query types
        test_queries = []
        
        if transcript:
            test_queries.append(("What was discussed in this conversation?", "general"))
        
        if analysis.get("transcript_summary"):
            summary_text = analysis.get("transcript_summary", "")
            words = summary_text.split()[:20]
            query_text = " ".join(words)
            test_queries.append((query_text, "summary-based"))
        
        if transcript:
            for turn in transcript[:3]:
                if turn.get("role") == "user" and turn.get("content"):
                    content = turn.get("content", "")
                    if len(content) > 20:
                        test_queries.append((content[:100], "user-message"))
                        break
        
        if not test_queries:
            test_queries.append(("conversation", "fallback"))
        
        for query, query_type in test_queries:
            print(f"\n  Query ({query_type}): '{query[:60]}...'")
            try:
                memories = await openmemory.query_memories(
                    query=query,
                    user_id=user_id,
                    limit=3
                )
                print(f"    Found {len(memories)} memories")
                if memories:
                    first_memory = memories[0]
                    content_preview = first_memory.get("content", "")
                    if len(content_preview) > 300:
                        content_preview = content_preview[:300] + "..."
                    print(f"    First memory preview: {content_preview}")
                    print(f"    Memory metadata: {first_memory.get('metadata', {})}")
                else:
                    print("    No memories found - this might indicate the content wasn't properly indexed")
            except Exception as e:
                print(f"    ✗ Error querying: {e}")
        
        # Step 6: Get user summary
        print("\nStep 4: Getting user summary...")
        try:
            summary = await openmemory.get_user_summary(user_id)
            if summary:
                print(f"✓ User summary available:")
                print(f"  {summary[:300]}...")
            else:
                print("  No summary available yet (may need multiple conversations or time to process)")
        except Exception as e:
            print(f"  Note: Could not get summary: {e}")
        
        # Step 7: Check what OpenMemory extracted
        print("\nStep 5: Checking stored memory details...")
        try:
            memories = await openmemory.query_memories(
                query="conversation",
                user_id=user_id,
                limit=1,
                filters={"conversation_id": conversation_id}
            )
            if memories:
                memory = memories[0]
                print(f"  Memory found with filters")
                print(f"  Metadata keys: {list(memory.get('metadata', {}).keys())}")
                content = memory.get("content", "")
                print(f"  Content length: {len(content)} chars")
                print(f"  Content type: {type(content)}")
                
                try:
                    parsed = json.loads(content)
                    print(f"  Content is valid JSON with keys: {list(parsed.keys())[:5]}")
                except:
                    print(f"  Content is plain text")
                
                preview = content[:400] if len(content) > 400 else content
                print(f"  Content preview:\n  {preview}...")
            else:
                print("  No memory found with conversation_id filter")
        except Exception as e:
            print(f"  Error checking memory details: {e}")
        
        # Step 8: Test with conversation-specific content
        print("\nStep 6: Testing search with conversation-specific content...")
        if transcript:
            conversation_text = ""
            for turn in transcript[:5]:
                role = turn.get("role", "")
                content = turn.get("content", "")
                if content:
                    conversation_text += f"{role}: {content}\n"
            
            if conversation_text:
                print(f"  Searching for specific conversation text...")
                try:
                    memories = await openmemory.query_memories(
                        query=conversation_text[:200],
                        user_id=user_id,
                        limit=1
                    )
                    if memories:
                        print(f"  ✓ Found memory with specific conversation text")
                        print(f"    This indicates OpenMemory is properly indexing the JSON content")
                    else:
                        print(f"  ⚠ Could not find memory with specific text")
                        print(f"    This might indicate the JSON structure is not optimal for search")
                except Exception as e:
                    print(f"  Error: {e}")
        
        print("\n" + "=" * 80)
        print("Test Summary:")
        print("=" * 80)
        print(f"✓ Conversation stored: {conversation_id}")
        print(f"✓ Memory ID: {memory_id}")
        print(f"✓ User ID: {user_id}")
        print("\nRecommendations:")
        print("1. Check if semantic queries return relevant results")
        print("2. Verify user summaries are generated (may need multiple conversations)")
        print("3. If search results are poor, consider extracting transcript text separately")
        print("4. If storage is inefficient, consider optimizing payload structure")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        logger.error(f"Error during test: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
    finally:
        await openmemory.close()


if __name__ == "__main__":
    print("\nStarting test...")
    print("Make sure OpenMemory is running and OPENMEMORY_API_KEY is set in environment\n")
    asyncio.run(test_post_call_storage())



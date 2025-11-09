"""Search data webhook handler for in-call memory search."""
from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any, Optional
import logging
from src.utils.auth import validate_header_auth
from src.clients.openmemory import OpenMemoryClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/search-data")
async def search_data_webhook(request: Request):
    """
    Handle search-data webhook for in-call memory search.
    
    This webhook is called as an Eleven Labs Tool during conversations
    to search OpenMemory for relevant context.
    """
    # Validate header authentication
    if not validate_header_auth(request):
        logger.error("Invalid authentication for search-data webhook")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )
    
    # Parse request body
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Error parsing search-data webhook body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body"
        )
    
    # Extract search parameters
    query = body.get("query") or body.get("search_query", "")
    user_id = body.get("user_id") or body.get("caller_id") or "unknown"
    limit = body.get("limit", 5)
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing query parameter"
        )
    
    # Query OpenMemory
    openmemory = OpenMemoryClient()
    try:
        memories = await openmemory.query_memories(
            query=query,
            user_id=user_id,
            limit=limit
        )
        
        # Format response for Eleven Labs Tool
        if memories:
            # Combine memories into a single response
            memory_texts = [mem.get("content", "") for mem in memories[:limit]]
            combined_context = "\n\n".join(memory_texts)
            
            return {
                "status": "success",
                "memories_found": len(memories),
                "context": combined_context,
                "memories": memories
            }
        else:
            return {
                "status": "success",
                "memories_found": 0,
                "context": "No relevant memories found.",
                "memories": []
            }
            
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memories"
        )
    finally:
        await openmemory.close()


"""Post-call webhook handler."""
from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any
import json
import logging
from utils.auth import validate_hmac_signature
from utils.helpers import extract_user_id_from_payload
from openmemory_client import OpenMemoryClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/post-call")
async def post_call_webhook(request: Request):
    """
    Handle post-call webhook from Eleven Labs.
    
    Stores entire post-call webhook payload to OpenMemory.
    """
    # Read request body once
    try:
        body = await request.body()
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error reading request body"
        )
    
    # Validate HMAC signature
    if not await validate_hmac_signature(request, body):
        logger.error("Invalid HMAC signature for post-call webhook")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Parse request body
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in post-call webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Extract user_id from payload
    user_id = extract_user_id_from_payload(payload)
    if not user_id:
        logger.warning("No user_id found in post-call webhook payload")
        # Use conversation_id as fallback
        user_id = payload.get("data", {}).get("conversation_id", "unknown")
    
    # Store entire payload to OpenMemory
    openmemory = OpenMemoryClient()
    try:
        result = await openmemory.store_post_call_payload(
            payload=payload,
            user_id=user_id
        )
        logger.info(f"Stored post-call webhook for user {user_id}")
        return {"status": "received", "memory_id": result.get("id")}
    except Exception as e:
        logger.error(f"Error storing post-call webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store memory"
        )
    finally:
        await openmemory.close()


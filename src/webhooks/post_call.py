"""Post-call webhook handler with HMAC validation first."""
from fastapi import APIRouter, Request, HTTPException, status, BackgroundTasks
from typing import Dict, Any, Optional
import json
import logging
import time
import hmac
from hashlib import sha256
from src.utils.helpers import extract_user_id_from_payload
from src.utils.webhook_storage import save_webhook_payload
from src.clients.openmemory import OpenMemoryClient
from src.clients.elevenlabs import ElevenLabsClient
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def store_agent_profile_background(
    agent_id: str,
    openmemory: Optional[OpenMemoryClient] = None,
    elevenlabs: Optional[ElevenLabsClient] = None
) -> None:
    """
    Background task to store agent profile.
    
    Args:
        agent_id: Agent ID
        openmemory: OpenMemory client (creates new if None)
        elevenlabs: Eleven Labs client (creates new if None)
    """
    # Create new clients if not provided
    if openmemory is None:
        openmemory = OpenMemoryClient()
    if elevenlabs is None:
        elevenlabs = ElevenLabsClient()
    
    try:
        # Check if agent profile is already cached
        cached_agent_data = await openmemory.get_agent_profile(agent_id)
        
        if not cached_agent_data:
            # Fetch and store agent profile
            logger.info(f"Fetching and storing agent profile for {agent_id} (background)")
            agent_data = await elevenlabs.get_agent(agent_id)
            
            if agent_data:
                await openmemory.store_agent_profile(agent_id, agent_data)
                logger.info(f"Stored agent profile for {agent_id} (background)")
            else:
                logger.warning(f"Agent {agent_id} not found in API (background)")
        else:
            logger.debug(f"Agent profile for {agent_id} already cached (background)")
    except Exception as e:
        logger.error(f"Error storing agent profile for {agent_id} (background): {e}", exc_info=True)
    finally:
        await openmemory.close()
        await elevenlabs.close()


@router.post("/post-call")
async def post_call_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle post-call webhook from Eleven Labs.
    
    Validates HMAC signature first, then stores files and processes webhook.
    """
    # 1. Read request body (payload)
    try:
        payload = await request.body()
    except Exception as e:
        logger.error(f"Error reading request body: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error reading request body"
        )
    
    # 2. Check HMAC header presence (FIRST CHECK - before everything else)
    headers = request.headers.get("elevenlabs-signature")
    if headers is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature header"
        )
    
    # 3. Parse timestamp and signature from header
    try:
        timestamp = headers.split(",")[0][2:]  # Extract timestamp (skip "t=")
        hmac_signature = headers.split(",")[1]  # Extract signature
    except (IndexError, ValueError) as e:
        logger.error(f"Invalid signature format: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature format"
        )
    
    # 4. Validate timestamp (30 minute tolerance)
    tolerance = int(time.time()) - 30 * 60
    try:
        if int(timestamp) < tolerance:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Timestamp too old"
            )
    except ValueError as e:
        logger.error(f"Invalid timestamp: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp"
        )
    
    # 5. Validate signature (HMAC SHA256 of timestamp.payload)
    try:
        full_payload_to_sign = f"{timestamp}.{payload.decode('utf-8')}"
        mac = hmac.new(
            key=settings.elevenlabs_webhook_secret.encode("utf-8"),
            msg=full_payload_to_sign.encode("utf-8"),
            digestmod=sha256,
        )
        digest = 'v0=' + mac.hexdigest()
        if not hmac.compare_digest(hmac_signature, digest):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )
    except UnicodeDecodeError as e:
        logger.error(f"Error decoding payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload encoding"
        )
    
    # 6. Parse JSON (needed to determine webhook type and extract data)
    try:
        payload_json = json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in post-call webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # 7. Store files (save webhook payload directly to main storage)
    try:
        save_webhook_payload(payload=payload_json, request_id=None, validated=True)
    except Exception as e:
        logger.error(f"Error saving webhook payload: {e}", exc_info=True)
        # Continue processing even if file save fails
    
    # 8. Process webhook (store to OpenMemory if transcription webhook)
    webhook_type = payload_json.get("type")
    if webhook_type == "post_call_transcription":
        # Extract user_id from payload (prioritizes system__caller_id for consistent caller identification)
        user_id = extract_user_id_from_payload(payload_json)
        if not user_id:
            logger.warning("No user_id found in post-call webhook payload")
            # Use conversation_id as last resort fallback
            user_id = payload_json.get("data", {}).get("conversation_id", "unknown")
            logger.warning(f"Using conversation_id as fallback user_id: {user_id}")
        
        # Extract agent_id from payload
        agent_id = payload_json.get("data", {}).get("agent_id")
        
        # Store entire payload to OpenMemory
        openmemory = OpenMemoryClient()
        try:
            # Store post-call payload
            result = await openmemory.store_post_call_payload(
                payload=payload_json,
                user_id=user_id
            )
            logger.info(f"Stored post-call webhook for user {user_id}, memory_id: {result.get('id')}")
            
            # Store agent profile in background if agent_id is present
            if agent_id:
                # Create new clients for background task (don't reuse main clients)
                background_tasks.add_task(
                    store_agent_profile_background,
                    agent_id,
                    None,  # Will create new client in background task
                    None   # Will create new client in background task
                )
                logger.debug(f"Scheduled background task to store agent profile for {agent_id}")
            
            await openmemory.close()
            
            return {
                "status": "received",
                "memory_id": result.get("id")
            }
        except Exception as e:
            logger.error(f"Error storing post-call webhook: {e}", exc_info=True)
            await openmemory.close()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store memory"
            )
    else:
        # For audio and failure webhooks, just acknowledge receipt
        logger.info(f"Received {webhook_type} webhook (not stored to OpenMemory)")
        return {
            "status": "received"
        }

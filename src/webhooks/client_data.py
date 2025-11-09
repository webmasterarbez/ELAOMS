"""Client data webhook handler for conversation initiation."""
from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any
import logging
from src.utils.auth import validate_header_auth
from src.utils.helpers import build_conversation_initiation_response
from src.clients.openmemory import OpenMemoryClient
from src.clients.elevenlabs import ElevenLabsClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def get_or_fetch_agent_profile(agent_id: str) -> Dict[str, Any]:
    """
    Get agent profile from OpenMemory cache or fetch from API.
    
    Args:
        agent_id: The agent ID
        
    Returns:
        Agent profile dictionary with extracted fields for backward compatibility
    """
    openmemory = OpenMemoryClient()
    elevenlabs = ElevenLabsClient()
    
    try:
        # Check OpenMemory cache first
        cached_agent_data = await openmemory.get_agent_profile(agent_id)
        
        if cached_agent_data:
            logger.info(f"Using cached agent profile for {agent_id}")
            # Extract fields for backward compatibility
            return elevenlabs.extract_agent_fields(cached_agent_data)
        
        # Fetch from API if not in cache
        logger.info(f"Fetching agent profile from API for {agent_id}")
        agent_data = await elevenlabs.get_agent(agent_id)
        
        if not agent_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Store in OpenMemory cache
        await openmemory.store_agent_profile(agent_id, agent_data)
        
        # Extract fields for backward compatibility
        return elevenlabs.extract_agent_fields(agent_data)
        
    finally:
        await elevenlabs.close()
        await openmemory.close()


@router.post("/client-data")
async def client_data_webhook(request: Request):
    """
    Handle client-data webhook for conversation initiation.
    
    Returns personalized conversation_initiation_client_data with
    AI-generated first message based on user's OpenMemory history.
    """
    # Validate header authentication
    if not validate_header_auth(request):
        logger.error("Invalid authentication for client-data webhook")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )
    
    # Parse request body (Twilio call parameters)
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Error parsing client-data webhook body: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request body"
        )
    
    caller_id = body.get("caller_id")
    agent_id = body.get("agent_id")
    called_number = body.get("called_number")
    call_sid = body.get("call_sid")
    
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing agent_id"
        )
    
    # Get or fetch agent profile
    agent_profile = await get_or_fetch_agent_profile(agent_id)
    
    # Use caller_id as user_id for OpenMemory
    # caller_id from Twilio webhook is the phone number, which is consistent for same caller
    user_id = caller_id or "unknown"
    
    # Query OpenMemory for user summary and generate personalized message
    openmemory = OpenMemoryClient()
    try:
        # Get user summary
        user_summary = await openmemory.get_user_summary(user_id)
        
        # Generate personalized first message
        personalized_message = await openmemory.generate_personalized_message(
            user_id=user_id,
            prompt="Generate a personalized first message for this user based on their conversation history. Make it warm, natural, and reference previous interactions if available."
        )
        
        # Build dynamic variables (required field)
        dynamic_variables = {
            "caller_id": caller_id or "",
            "called_number": called_number or "",
            "call_sid": call_sid or ""
        }
        
        # If we have user summary, add it to dynamic variables
        if user_summary:
            dynamic_variables["user_context"] = user_summary[:500]  # Limit length
        
        # Build response with personalized first message
        response = build_conversation_initiation_response(
            dynamic_variables=dynamic_variables,
            first_message=personalized_message or agent_profile.get("first_message"),
            language=agent_profile.get("language"),
            voice_id=agent_profile.get("voice_id")
        )
        
        logger.info(f"Generated personalized response for caller {caller_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating personalized message: {e}")
        # Fallback to default agent configuration
        response = build_conversation_initiation_response(
            dynamic_variables={
                "caller_id": caller_id or "",
                "called_number": called_number or "",
                "call_sid": call_sid or ""
            },
            first_message=agent_profile.get("first_message"),
            language=agent_profile.get("language"),
            voice_id=agent_profile.get("voice_id")
        )
        return response
    finally:
        await openmemory.close()


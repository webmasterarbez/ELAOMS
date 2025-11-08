"""Client data webhook handler for conversation initiation."""
from fastapi import APIRouter, Request, HTTPException, status
from typing import Dict, Any
import logging
from utils.auth import validate_header_auth
from utils.helpers import build_conversation_initiation_response
from openmemory_client import OpenMemoryClient
from elevenlabs_client import ElevenLabsClient
from database import get_db, Agent
from sqlalchemy.orm import Session
from fastapi import Depends

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


async def get_or_fetch_agent_profile(agent_id: str, db: Session) -> Dict[str, Any]:
    """
    Get agent profile from cache or fetch from API.
    
    Args:
        agent_id: The agent ID
        db: Database session
        
    Returns:
        Agent profile dictionary
    """
    # Check database cache
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    
    if agent:
        logger.info(f"Using cached agent profile for {agent_id}")
        return {
            "agent_id": agent.agent_id,
            "title": agent.title,
            "first_message": agent.first_message,
            "system_prompt": agent.system_prompt,
            "language": agent.language,
            "voice_id": agent.voice_id
        }
    
    # Fetch from API
    logger.info(f"Fetching agent profile from API for {agent_id}")
    elevenlabs = ElevenLabsClient()
    try:
        profile = await elevenlabs.build_agent_profile(agent_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Store in database cache
        agent = Agent(**profile)
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return profile
    finally:
        await elevenlabs.close()


@router.post("/client-data")
async def client_data_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
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
    agent_profile = await get_or_fetch_agent_profile(agent_id, db)
    
    # Use caller_id as user_id for OpenMemory
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


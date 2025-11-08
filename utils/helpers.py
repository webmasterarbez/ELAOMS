"""Helper utility functions."""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_user_id_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract user_id from post-call webhook payload.
    
    Args:
        payload: Post-call webhook payload
        
    Returns:
        User ID or None if not found
    """
    # Try multiple possible locations for user_id
    data = payload.get("data", {})
    
    # Check metadata.user_id
    user_id = data.get("metadata", {}).get("user_id")
    if user_id:
        return user_id
    
    # Check conversation_initiation_client_data.user_id
    user_id = data.get("conversation_initiation_client_data", {}).get("user_id")
    if user_id:
        return user_id
    
    # Check dynamic_variables for user_id
    dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    user_id = dynamic_vars.get("user_id")
    if user_id:
        return user_id
    
    return None


def build_conversation_initiation_response(
    dynamic_variables: Dict[str, Any],
    first_message: Optional[str] = None,
    system_prompt: Optional[str] = None,
    language: Optional[str] = None,
    voice_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build conversation_initiation_client_data response.
    
    Args:
        dynamic_variables: Dynamic variables for the agent
        first_message: Optional personalized first message
        system_prompt: Optional system prompt override
        language: Optional language override
        voice_id: Optional voice ID override
        
    Returns:
        conversation_initiation_client_data dictionary
    """
    response = {
        "type": "conversation_initiation_client_data",
        "dynamic_variables": dynamic_variables
    }
    
    # Build conversation_config_override if any overrides are provided
    overrides = {}
    if system_prompt or first_message or language:
        agent_overrides = {}
        if system_prompt:
            agent_overrides["prompt"] = {"prompt": system_prompt}
        if first_message:
            agent_overrides["first_message"] = first_message
        if language:
            agent_overrides["language"] = language
        
        if agent_overrides:
            overrides["agent"] = agent_overrides
    
    if voice_id:
        overrides["tts"] = {"voice_id": voice_id}
    
    if overrides:
        response["conversation_config_override"] = overrides
    
    return response


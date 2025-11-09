"""Helper utility functions."""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_user_id_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract user_id from post-call webhook payload.
    
    Priority order:
    1. system__caller_id from dynamic_variables (most consistent for same caller)
    2. user_id from conversation_initiation_client_data
    3. user_id from metadata
    4. user_id from dynamic_variables
    5. caller_id from metadata
    
    The user_id is normalized to ensure consistent storage:
    - Phone numbers are kept with + prefix for consistency
    - All values are converted to strings
    
    Args:
        payload: Post-call webhook payload
        
    Returns:
        User ID or None if not found
    """
    data = payload.get("data", {})
    
    # Priority 1: system__caller_id from dynamic_variables (most consistent for same caller)
    dynamic_vars = data.get("conversation_initiation_client_data", {}).get("dynamic_variables", {})
    caller_id = dynamic_vars.get("system__caller_id")
    if caller_id:
        user_id = str(caller_id).strip()
        logger.info(f"Using system__caller_id as user_id: {user_id}")
        return user_id
    
    # Priority 2: user_id from conversation_initiation_client_data
    user_id = data.get("conversation_initiation_client_data", {}).get("user_id")
    if user_id:
        user_id = str(user_id).strip()
        logger.info(f"Using conversation_initiation_client_data.user_id: {user_id}")
        return user_id
    
    # Priority 3: user_id from metadata
    user_id = data.get("metadata", {}).get("user_id")
    if user_id:
        user_id = str(user_id).strip()
        logger.info(f"Using metadata.user_id: {user_id}")
        return user_id
    
    # Priority 4: user_id from dynamic_variables
    user_id = dynamic_vars.get("user_id")
    if user_id:
        user_id = str(user_id).strip()
        logger.info(f"Using dynamic_variables.user_id: {user_id}")
        return user_id
    
    # Priority 5: caller_id from metadata (phone number)
    caller_id = data.get("metadata", {}).get("caller_id") or data.get("metadata", {}).get("from")
    if caller_id:
        user_id = str(caller_id).strip()
        logger.info(f"Using metadata.caller_id: {user_id}")
        return user_id
    
    logger.warning("No user_id found in payload")
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


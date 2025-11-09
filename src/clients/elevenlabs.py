"""Eleven Labs API client for fetching agent configuration."""
import httpx
import asyncio
from typing import Dict, Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


class ElevenLabsClient:
    """Client for interacting with Eleven Labs Agents API."""
    
    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def get_agent(self, agent_id: str, max_retries: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch agent configuration from Eleven Labs API with retry logic.
        
        Args:
            agent_id: The agent ID to fetch
            max_retries: Maximum number of retry attempts (defaults to settings.max_retries)
            
        Returns:
            Complete agent configuration dictionary from API or None if not found
        """
        if max_retries is None:
            max_retries = settings.max_retries
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.get(f"/convai/agents/{agent_id}")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Agent {agent_id} not found")
                    return None
                # Don't retry on 4xx errors (except 429 rate limit)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    logger.error(f"Error fetching agent {agent_id}: {e}")
                    raise
                last_exception = e
            except httpx.HTTPError as e:
                last_exception = e
            
            # Retry with exponential backoff
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, ...
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} for agent {agent_id} after {wait_time}s",
                    extra={"agent_id": agent_id, "attempt": attempt + 1, "max_retries": max_retries}
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Failed to fetch agent {agent_id} after {max_retries} retries: {last_exception}",
                    extra={"agent_id": agent_id, "max_retries": max_retries}
                )
                raise last_exception
        
        return None
    
    def extract_agent_fields(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract commonly used fields from agent data for backward compatibility.
        
        Args:
            agent_data: Complete agent data from API
            
        Returns:
            Dictionary with extracted fields: agent_id, title, first_message, system_prompt, language, voice_id
        """
        # Navigate the nested structure from the API response
        agent_config = agent_data.get("conversation_config", {})
        agent_info = agent_config.get("agent", {})
        tts_config = agent_config.get("tts", {})
        
        return {
            "agent_id": agent_data.get("agent_id"),
            "title": agent_data.get("name"),
            "first_message": agent_info.get("first_message"),
            "system_prompt": agent_info.get("prompt", {}).get("prompt") if isinstance(agent_info.get("prompt"), dict) else agent_info.get("prompt"),
            "language": agent_info.get("language"),
            "voice_id": tts_config.get("voice_id")
        }
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


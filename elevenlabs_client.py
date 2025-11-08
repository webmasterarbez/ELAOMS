"""Eleven Labs API client for fetching agent configuration."""
import httpx
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
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch agent configuration from Eleven Labs API.
        
        Args:
            agent_id: The agent ID to fetch
            
        Returns:
            Agent configuration dictionary or None if not found
        """
        try:
            response = await self.client.get(f"/agents/{agent_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Agent {agent_id} not found")
                return None
            logger.error(f"Error fetching agent {agent_id}: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Error fetching agent {agent_id}: {e}")
            raise
    
    async def build_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Build agent profile from API response.
        
        Args:
            agent_id: The agent ID to build profile for
            
        Returns:
            Agent profile dictionary with title, first_message, system_prompt, etc.
        """
        agent_data = await self.get_agent(agent_id)
        if not agent_data:
            return None
        
        # Extract relevant fields from agent data
        profile = {
            "agent_id": agent_id,
            "title": agent_data.get("name") or agent_data.get("title"),
            "first_message": agent_data.get("first_message"),
            "system_prompt": agent_data.get("prompt", {}).get("prompt") if isinstance(agent_data.get("prompt"), dict) else agent_data.get("prompt"),
            "language": agent_data.get("language"),
            "voice_id": agent_data.get("voice_id")
        }
        
        return profile
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


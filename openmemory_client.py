"""OpenMemory API client wrapper."""
import httpx
from typing import Dict, Any, Optional, List
from config import settings
import logging

logger = logging.getLogger(__name__)


class OpenMemoryClient:
    """Client for interacting with OpenMemory API."""
    
    def __init__(self):
        self.base_url = settings.openmemory_url.rstrip("/")
        self.api_key = settings.openmemory_api_key
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
        """
        Store a memory in OpenMemory.
        
        Args:
            content: The memory content to store
            user_id: User ID for memory isolation
            metadata: Optional metadata filters
            
        Returns:
            Response from OpenMemory API
        """
        payload = {
            "content": content,
            "filters": {
                "user_id": user_id,
                **(metadata or {})
            }
        }
        
        try:
            response = await self.client.post("/memories", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error storing memory: {e}")
            raise
    
    async def query_memories(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query memories from OpenMemory.
        
        Args:
            query: Search query string
            user_id: User ID for memory isolation
            limit: Maximum number of results
            filters: Optional additional filters
            
        Returns:
            List of matching memories
        """
        payload = {
            "query": query,
            "limit": limit,
            "filters": {
                "user_id": user_id,
                **(filters or {})
            }
        }
        
        try:
            response = await self.client.post("/memories/query", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("memories", [])
        except httpx.HTTPError as e:
            logger.error(f"Error querying memories: {e}")
            raise
    
    async def get_user_summary(self, user_id: str) -> Optional[str]:
        """
        Get user summary from OpenMemory.
        
        Args:
            user_id: User ID to get summary for
            
        Returns:
            User summary string or None if not available
        """
        try:
            response = await self.client.get(f"/users/{user_id}/summary")
            response.raise_for_status()
            result = response.json()
            return result.get("summary")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.info(f"No summary found for user {user_id}")
                return None
            logger.error(f"Error getting user summary: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Error getting user summary: {e}")
            raise
    
    async def store_post_call_payload(
        self,
        payload: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Store entire post-call webhook payload to OpenMemory.
        
        Args:
            payload: Complete post_call_transcription webhook payload
            user_id: User ID for memory isolation
            
        Returns:
            Response from OpenMemory API
        """
        # Convert entire payload to JSON string for storage
        import json
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
    
    async def generate_personalized_message(
        self,
        user_id: str,
        prompt: str = "Generate a personalized first message for this user based on their conversation history"
    ) -> Optional[str]:
        """
        Generate a personalized first message using OpenMemory's query API.
        
        Args:
            user_id: User ID to generate message for
            prompt: Prompt for generating the personalized message
            
        Returns:
            Generated personalized message or None if generation fails
        """
        try:
            # First get user summary for context
            user_summary = await self.get_user_summary(user_id)
            
            # Build query with user summary context
            if user_summary:
                full_query = f"{prompt}\n\nUser context:\n{user_summary}"
            else:
                full_query = prompt
            
            # Query OpenMemory to generate personalized message
            memories = await self.query_memories(
                query=full_query,
                user_id=user_id,
                limit=5
            )
            
            # If we have memories, use the most relevant one or combine them
            if memories:
                # For now, return a simple personalized message
                # In production, you might want to use an LLM to generate from memories
                return f"Hi! Welcome back. Based on our previous conversations, I'm here to help you."
            
            return None
        except Exception as e:
            logger.error(f"Error generating personalized message: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


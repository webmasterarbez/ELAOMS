"""Authentication utilities for webhooks."""
import time
import hmac
from hashlib import sha256
from fastapi import Request, HTTPException, status
from config import settings
import logging

logger = logging.getLogger(__name__)


async def validate_hmac_signature(request: Request, body_bytes: bytes) -> bool:
    """
    Validate HMAC signature for post-call-webhook.
    
    Args:
        request: FastAPI request object
        body_bytes: Request body bytes (must be passed separately to avoid reading twice)
        
    Returns:
        True if signature is valid, False otherwise
    """
    signature_header = request.headers.get("elevenlabs-signature")
    if not signature_header:
        logger.warning("Missing ElevenLabs-Signature header")
        return False
    
    try:
        # Parse signature header: t=timestamp,v0=hash
        parts = signature_header.split(",")
        timestamp_part = parts[0]
        hmac_part = parts[1] if len(parts) > 1 else None
        
        if not hmac_part:
            logger.warning("Invalid signature format")
            return False
        
        # Extract timestamp
        timestamp = timestamp_part.split("=")[1]
        
        # Validate timestamp (30 minute tolerance)
        current_time = int(time.time())
        tolerance = 30 * 60  # 30 minutes in seconds
        if int(timestamp) < (current_time - tolerance):
            logger.warning("Timestamp too old")
            return False
        
        # Get request body string
        body_str = body_bytes.decode('utf-8')
        
        # Compute expected signature
        payload_to_sign = f"{timestamp}.{body_str}"
        mac = hmac.new(
            key=settings.elevenlabs_webhook_secret.encode("utf-8"),
            msg=payload_to_sign.encode("utf-8"),
            digestmod=sha256
        )
        expected_digest = 'v0=' + mac.hexdigest()
        
        # Compare signatures
        if hmac_part != expected_digest:
            logger.warning("HMAC signature mismatch")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating HMAC signature: {e}")
        return False


def validate_header_auth(request: Request) -> bool:
    """
    Validate header-based authentication for client-data and search-data webhooks.
    
    Note: This is a placeholder. In production, you should validate
    the headers based on secrets configured in ElevenLabs secrets manager.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if authentication is valid, False otherwise
    """
    # TODO: Implement actual header validation based on ElevenLabs secrets manager
    # For now, we'll check for presence of common auth headers
    auth_header = request.headers.get("authorization") or request.headers.get("x-api-key")
    
    if not auth_header:
        logger.warning("Missing authentication header")
        return False
    
    # In production, validate against secrets from ElevenLabs secrets manager
    return True


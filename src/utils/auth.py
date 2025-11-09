"""Authentication utilities for webhooks."""
import time
import hmac
import hashlib
from hashlib import sha256
from typing import Tuple, Optional
from fastapi import Request, HTTPException, status
from config import settings
import logging
import uuid

logger = logging.getLogger(__name__)


async def validate_hmac_signature(request: Request, body_bytes: bytes, request_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate HMAC signature for post-call-webhook with enhanced logging and audit trail.
    
    Args:
        request: FastAPI request object
        body_bytes: Request body bytes (must be passed separately to avoid reading twice)
        request_id: Request ID for tracking (generated if not provided)
        
    Returns:
        Tuple of (is_valid, request_id)
    """
    if not request_id:
        request_id = str(uuid.uuid4())
    
    signature_header = request.headers.get("elevenlabs-signature")
    if not signature_header:
        logger.warning(
            f"HMAC validation failed: Missing ElevenLabs-Signature header",
            extra={
                "request_id": request_id,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "payload_hash": hashlib.sha256(body_bytes).hexdigest()[:16]
            }
        )
        return False, request_id
    
    try:
        # Parse signature header: t=timestamp,v0=hash
        parts = signature_header.split(",")
        timestamp_part = parts[0]
        hmac_part = parts[1] if len(parts) > 1 else None
        
        if not hmac_part:
            logger.warning(
                f"HMAC validation failed: Invalid signature format",
                extra={
                    "request_id": request_id,
                    "signature_header": signature_header[:50] if len(signature_header) > 50 else signature_header,
                    "client_ip": request.client.host if request.client else None
                }
            )
            return False, request_id
        
        # Extract timestamp
        timestamp = timestamp_part.split("=")[1]
        
        # Validate timestamp (30 minute tolerance)
        current_time = int(time.time())
        timestamp_int = int(timestamp)
        tolerance = 30 * 60  # 30 minutes in seconds
        age = current_time - timestamp_int
        
        # Reject both too-old timestamps (age > tolerance) and future timestamps (age < 0)
        # This prevents replay attacks with future-dated signatures
        if age < 0 or age > tolerance:
            reason = "Timestamp in the future" if age < 0 else f"Timestamp too old (age: {age}s, tolerance: {tolerance}s)"
            logger.warning(
                f"HMAC validation failed: {reason}",
                extra={
                    "request_id": request_id,
                    "timestamp": timestamp_int,
                    "current_time": current_time,
                    "age_seconds": age,
                    "client_ip": request.client.host if request.client else None
                }
            )
            return False, request_id
        
        # Get request body string
        body_str = body_bytes.decode('utf-8')
        
        # Compute expected signature
        payload_to_sign = f"{timestamp}.{body_str}"
        mac = hmac.new(
            key=settings.elevenlabs_post_call_hmac_key.encode("utf-8"),
            msg=payload_to_sign.encode("utf-8"),
            digestmod=sha256
        )
        expected_digest = 'v0=' + mac.hexdigest()
        
        # Compare signatures using constant-time comparison
        if not hmac.compare_digest(hmac_part, expected_digest):
            logger.warning(
                f"HMAC validation failed: Signature mismatch",
                extra={
                    "request_id": request_id,
                    "timestamp": timestamp_int,
                    "age_seconds": age,
                    "client_ip": request.client.host if request.client else None,
                    "payload_hash": hashlib.sha256(body_bytes).hexdigest()[:16],
                    "user_agent": request.headers.get("user-agent")
                }
            )
            return False, request_id
        
        logger.info(
            f"HMAC validation successful",
            extra={
                "request_id": request_id,
                "timestamp": timestamp_int,
                "age_seconds": age,
                "client_ip": request.client.host if request.client else None
            }
        )
        return True, request_id
    except Exception as e:
        logger.error(
            f"Error validating HMAC signature: {e}",
            extra={
                "request_id": request_id,
                "client_ip": request.client.host if request.client else None,
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        return False, request_id


def validate_header_auth(request: Request) -> bool:
    """
    Validate header-based authentication for client-data and search-data webhooks.
    
    Validates the X-Api-Key header against the configured client-data workspace secret.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if authentication is valid, False otherwise
    """
    # Get API key from header (case-insensitive)
    api_key = request.headers.get("x-api-key") or request.headers.get("X-Api-Key")
    
    if not api_key:
        logger.warning(
            "Missing X-Api-Key header",
            extra={
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        return False
    
    # Check if client-data workspace secret is configured
    if not settings.elevenlabs_client_data_workspace_secret:
        logger.error(
            "Client-data workspace secret not configured in settings",
            extra={
                "client_ip": request.client.host if request.client else None
            }
        )
        return False
    
    # Validate API key using constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(api_key, settings.elevenlabs_client_data_workspace_secret):
        logger.warning(
            "Invalid X-Api-Key header value",
            extra={
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else "***"
            }
        )
        return False
    
    logger.info(
        "Header authentication successful",
        extra={
            "client_ip": request.client.host if request.client else None
        }
    )
    return True


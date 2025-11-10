"""Utility functions for webhook file storage with security and performance enhancements."""
import os
import json
import base64
import logging
import re
import shutil
import time
import uuid
import stat
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from config import settings
from src.utils.helpers import extract_user_id_from_payload
from src.utils.anomaly_detection import record_quarantine_failure

logger = logging.getLogger(__name__)

# In-memory cache for audio webhooks waiting for transcription
# Structure: {conversation_id: {"audio_data": bytes, "timestamp": float}}
_audio_webhook_cache: Dict[str, Dict[str, Any]] = {}

# Redis client (optional, for distributed caching)
_redis_client: Optional[Any] = None


def get_redis_client():
    """
    Get or create Redis client for distributed caching.
    
    Returns:
        Redis client or None if Redis is not configured
    """
    global _redis_client
    
    if not settings.redis_url:
        return None
    
    if _redis_client is None:
        try:
            import redis.asyncio as redis
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False  # We need bytes for audio data
            )
            logger.info("Redis client initialized for distributed caching")
        except ImportError:
            logger.warning("Redis not available, falling back to in-memory cache")
            return None
        except Exception as e:
            logger.error(f"Error initializing Redis client: {e}")
            return None
    
    return _redis_client


def sanitize_filename(identifier: str) -> str:
    """
    Enhanced sanitization for identifiers with comprehensive edge case handling.
    
    Removes or replaces unsafe characters (path traversal, special chars, unicode issues).
    
    Args:
        identifier: Identifier to sanitize (phone number, agent_id, conversation_id)
        
    Returns:
        Sanitized identifier safe for filesystem usage
    """
    if not identifier:
        return "unknown"
    
    # Convert to string if not already
    identifier = str(identifier)
    
    # Remove path traversal attempts (multiple patterns)
    identifier = identifier.replace("..", "")
    identifier = identifier.replace("../", "")
    identifier = identifier.replace("..\\", "")
    identifier = identifier.replace("/", "_")
    identifier = identifier.replace("\\", "_")
    
    # Remove or replace special characters (comprehensive list)
    # Windows reserved names
    reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5", 
                      "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", 
                      "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    if identifier.upper() in reserved_names:
        identifier = f"_{identifier}_"
    
    # Remove or replace special characters
    identifier = re.sub(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', '_', identifier)
    
    # Remove leading/trailing dots and spaces (Windows issue)
    identifier = identifier.strip('. ')
    
    # Remove control characters and normalize unicode
    try:
        identifier = identifier.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        # If encoding fails, use a safe fallback
        identifier = re.sub(r'[^\w\-_\.]', '_', identifier)
    
    # Limit length to prevent filesystem issues
    max_length = 255
    if len(identifier) > max_length:
        # Truncate but preserve extension if present
        identifier = identifier[:max_length]
    
    # Ensure not empty after sanitization
    if not identifier or identifier.strip() == "":
        return "unknown"
    
    return identifier


def sanitize_path(path: str) -> str:
    """
    Sanitize full path for safe filesystem usage.
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    # Normalize path separators
    path = os.path.normpath(path)
    
    # Remove any remaining path traversal
    parts = path.split(os.sep)
    sanitized_parts = [sanitize_filename(part) for part in parts]
    
    return os.path.join(*sanitized_parts)


def extract_caller_phone_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    """
    Extract caller phone number from webhook payload.
    
    Uses same priority as extract_user_id_from_payload to get phone number.
    
    Args:
        payload: Webhook payload
        
    Returns:
        Phone number string or None if not found
    """
    return extract_user_id_from_payload(payload)


def cache_audio_webhook(conversation_id: str, audio_data: bytes) -> None:
    """
    Cache audio webhook temporarily until transcription arrives.
    
    Uses Redis if available, otherwise falls back to in-memory cache.
    Includes timestamp for TTL-based expiration.
    
    Args:
        conversation_id: Conversation ID
        audio_data: Decoded audio bytes
    """
    redis_client = get_redis_client()
    
    if redis_client:
        # Use Redis for distributed caching
        try:
            import asyncio
            cache_key = f"audio_webhook:{conversation_id}"
            # Store as base64 for Redis
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            cache_data = json.dumps({
                "audio_data": audio_b64,
                "timestamp": time.time()
            })
            # Use asyncio.run for sync context (or make this async)
            # For now, use sync Redis operations
            try:
                import redis
                sync_redis = redis.from_url(settings.redis_url, decode_responses=True)
                sync_redis.setex(cache_key, settings.redis_ttl, cache_data)
                logger.info(f"Cached audio webhook in Redis for conversation {conversation_id}")
            except Exception as e:
                logger.warning(f"Redis cache failed, falling back to in-memory: {e}")
                # Fall through to in-memory cache
                redis_client = None
        except Exception as e:
            logger.warning(f"Error using Redis cache: {e}, falling back to in-memory")
            redis_client = None
    
    if not redis_client:
        # Fall back to in-memory cache
        _audio_webhook_cache[conversation_id] = {
            "audio_data": audio_data,
            "timestamp": time.time()
        }
        logger.info(f"Cached audio webhook in memory for conversation {conversation_id}")


def get_cached_audio_webhook(conversation_id: str) -> Optional[bytes]:
    """
    Get cached audio webhook if not expired.
    
    Checks Redis first, then falls back to in-memory cache.
    
    Args:
        conversation_id: Conversation ID
        
    Returns:
        Cached audio bytes or None if not found or expired
    """
    redis_client = get_redis_client()
    
    if redis_client:
        # Try Redis first
        try:
            import redis
            sync_redis = redis.from_url(settings.redis_url, decode_responses=True)
            cache_key = f"audio_webhook:{conversation_id}"
            cache_data = sync_redis.get(cache_key)
            
            if cache_data:
                cache_entry = json.loads(cache_data)
                # Check if expired
                age = time.time() - cache_entry["timestamp"]
                if age > settings.audio_cache_ttl:
                    sync_redis.delete(cache_key)
                    logger.info(f"Audio cache entry for {conversation_id} expired (age: {age:.0f}s)")
                    return None
                
                # Decode base64 audio data
                audio_data = base64.b64decode(cache_entry["audio_data"])
                logger.info(f"Retrieved audio webhook from Redis for conversation {conversation_id}")
                return audio_data
        except Exception as e:
            logger.warning(f"Error retrieving from Redis cache: {e}, checking in-memory")
    
    # Fall back to in-memory cache
    cache_entry = _audio_webhook_cache.get(conversation_id)
    if not cache_entry:
        return None
    
    # Check if expired
    age = time.time() - cache_entry["timestamp"]
    if age > settings.audio_cache_ttl:
        logger.info(f"Audio cache entry for {conversation_id} expired (age: {age:.0f}s)")
        del _audio_webhook_cache[conversation_id]
        return None
    
    return cache_entry["audio_data"]


def cleanup_expired_cache_entries() -> int:
    """
    Clean up expired audio cache entries.
    
    Returns:
        Number of entries cleaned up
    """
    current_time = time.time()
    expired_keys = [
        key for key, entry in _audio_webhook_cache.items()
        if (current_time - entry["timestamp"]) > settings.audio_cache_ttl
    ]
    
    for key in expired_keys:
        del _audio_webhook_cache[key]
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired audio cache entries")
    
    return len(expired_keys)


def process_cached_audio_webhook(conversation_id: str, caller_phone: Optional[str]) -> Optional[str]:
    """
    Process cached audio webhook when transcription arrives.
    
    Args:
        conversation_id: Conversation ID
        caller_phone: Caller phone number (can be None, will use conversation_id as fallback)
        
    Returns:
        File path where audio was saved or None if no cached audio
    """
    audio_data = get_cached_audio_webhook(conversation_id)
    if not audio_data:
        logger.debug(f"No cached audio data found for conversation {conversation_id}. Audio webhook may not have been received, expired from cache (TTL: {settings.audio_cache_ttl}s), or failed to cache.")
        return None
    
    # Save audio file (save_webhook_to_file handles None caller_phone by using conversation_id)
    file_path = save_webhook_to_file(
        payload=None,  # Not needed for audio
        webhook_type="audio",
        conversation_id=conversation_id,
        caller_phone=caller_phone,  # Can be None
        audio_data=audio_data,
        validated=True  # Already validated since transcription arrived
    )
    
    # Remove from cache
    if conversation_id in _audio_webhook_cache:
        del _audio_webhook_cache[conversation_id]
    
    logger.info(f"Processed and saved cached audio webhook for conversation {conversation_id}")
    return file_path


def save_webhook_metadata(
    file_path: str,
    webhook_type: str,
    validated: bool = False,
    request_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Save metadata file for webhook storage.
    
    Args:
        file_path: Path to webhook file
        webhook_type: Type of webhook
        validated: Whether webhook passed HMAC validation
        request_id: Request ID for tracking
        **kwargs: Additional metadata fields
        
    Returns:
        Path to metadata file
    """
    metadata_path = file_path + ".metadata.json"
    metadata = {
        "webhook_type": webhook_type,
        "validated": validated,
        "timestamp": datetime.utcnow().isoformat(),
        "file_path": file_path,
        "request_id": request_id or str(uuid.uuid4()),
        **kwargs
    }
    
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.debug(f"Saved metadata file: {metadata_path}")
    except Exception as e:
        logger.error(f"Error saving metadata file: {e}")
    
    return metadata_path


def save_webhook_to_file(
    payload: Optional[Dict[str, Any]],
    webhook_type: str,
    conversation_id: str,
    caller_phone: Optional[str] = None,
    agent_id: Optional[str] = None,
    audio_data: Optional[bytes] = None,
    validated: bool = False,
    request_id: Optional[str] = None,
    use_quarantine: bool = False
) -> str:
    """
    Save webhook payload to file.
    
    File structure: {WEBHOOK_STORAGE_PATH}/{directory}/{conversation_id}_{type}.{ext}
    Directory priority: agent_id > caller_phone > conversation_id
    
    Args:
        payload: Webhook payload (for JSON types)
        webhook_type: Type of webhook (transcription, audio, failure)
        conversation_id: Conversation ID
        caller_phone: Caller phone number (directory name, for transcription/audio)
        agent_id: Agent ID (directory name, for failure webhooks)
        audio_data: Audio bytes (for audio webhooks)
        validated: Whether webhook passed HMAC validation
        request_id: Request ID for tracking
        use_quarantine: Whether to save to quarantine directory
        
    Returns:
        File path where webhook was saved
    """
    # Sanitize identifiers
    conversation_id = sanitize_filename(conversation_id)
    caller_phone = sanitize_filename(caller_phone) if caller_phone else None
    agent_id = sanitize_filename(agent_id) if agent_id else None
    
    # Determine file extension and content
    if webhook_type == "audio":
        file_ext = "mp3"
        if not audio_data:
            raise ValueError("audio_data is required for audio webhooks")
        content = audio_data
    else:
        file_ext = "json"
        if not payload:
            raise ValueError("payload is required for non-audio webhooks")
        content = json.dumps(payload, indent=2).encode('utf-8')
    
    # Determine directory name: agent_id > caller_phone > conversation_id
    directory_name = agent_id or caller_phone or conversation_id
    
    # Choose base path (quarantine or main storage)
    if use_quarantine:
        base_path = settings.webhook_quarantine_path
    else:
        base_path = settings.webhook_storage_path
    
    # Create directory path
    directory_path = os.path.join(base_path, directory_name)
    os.makedirs(directory_path, exist_ok=True)
    
    # Build file path
    filename = f"{conversation_id}_{webhook_type}.{file_ext}"
    file_path = os.path.join(directory_path, filename)
    
    # Sanitize full path
    file_path = sanitize_path(file_path)
    
    # Handle file conflicts by appending timestamp
    if os.path.exists(file_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{conversation_id}_{webhook_type}_{timestamp}.{file_ext}"
        file_path = os.path.join(directory_path, filename)
        logger.warning(f"File exists, saving as {filename}")
    
    # Write file with secure permissions
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Set file permissions (read/write for owner only by default)
    try:
        os.chmod(file_path, settings.file_permissions_mode)
    except Exception as e:
        logger.warning(f"Error setting file permissions for {file_path}: {e}")
    
    # Set directory permissions (read/write/execute for owner only)
    try:
        os.chmod(directory_path, 0o700)  # drwx------
    except Exception as e:
        logger.warning(f"Error setting directory permissions for {directory_path}: {e}")
    
    # Encryption at rest (if enabled)
    if settings.enable_encryption_at_rest:
        try:
            from cryptography.fernet import Fernet
            # Note: In production, use a proper key management system
            # This is a placeholder - you should load the key from secure storage
            encryption_key = os.getenv("ENCRYPTION_KEY")
            if encryption_key:
                fernet = Fernet(encryption_key.encode())
                with open(file_path, 'rb') as f:
                    encrypted_data = fernet.encrypt(f.read())
                with open(file_path, 'wb') as f:
                    f.write(encrypted_data)
                logger.debug(f"Encrypted file at rest: {file_path}")
        except ImportError:
            logger.warning("Encryption requested but cryptography not installed")
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
    
    # Save metadata
    file_size = len(content)
    save_webhook_metadata(
        file_path=file_path,
        webhook_type=webhook_type,
        validated=validated,
        request_id=request_id,
        file_size=file_size,
        directory_name=directory_name
    )
    
    logger.info(f"Saved {webhook_type} webhook to {file_path} (validated: {validated})")
    return file_path


def move_file_from_quarantine(quarantine_path: str, validated: bool = True) -> Optional[str]:
    """
    Move file from quarantine to main storage after validation.
    
    Args:
        quarantine_path: Path to file in quarantine
        validated: Whether validation passed
        
    Returns:
        New file path in main storage, or None if move failed
    """
    if not os.path.exists(quarantine_path):
        logger.warning(f"Quarantine file not found: {quarantine_path}")
        return None
    
    # Determine target directory based on file location
    # Extract directory structure from quarantine path
    relative_path = os.path.relpath(quarantine_path, settings.webhook_quarantine_path)
    target_path = os.path.join(settings.webhook_storage_path, relative_path)
    
    # Create target directory
    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    
    try:
        # Move file
        shutil.move(quarantine_path, target_path)
        
        # Move metadata file if exists
        metadata_path = quarantine_path + ".metadata.json"
        if os.path.exists(metadata_path):
            target_metadata_path = target_path + ".metadata.json"
            shutil.move(metadata_path, target_metadata_path)
            
            # Update metadata with validation status
            try:
                with open(target_metadata_path, 'r') as f:
                    metadata = json.load(f)
                metadata["validated"] = validated
                metadata["moved_at"] = datetime.utcnow().isoformat()
                with open(target_metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            except Exception as e:
                logger.error(f"Error updating metadata after move: {e}")
        
        logger.info(f"Moved file from quarantine to {target_path}")
        return target_path
    except Exception as e:
        logger.error(f"Error moving file from quarantine: {e}")
        return None


def save_webhook_payload(
    payload: Dict[str, Any],
    request_id: Optional[str] = None,
    validated: bool = False
) -> Optional[str]:
    """
    Save webhook payload to file based on webhook type.
    
    Handles three webhook types:
    - post_call_transcription: Save immediately, process cached audio if exists
    - post_call_audio: Cache temporarily (don't save yet)
    - call_initiation_failure: Save immediately
    
    Args:
        payload: Webhook payload
        request_id: Request ID for tracking
        validated: Whether webhook passed HMAC validation
        
    Returns:
        File path where webhook was saved, or None if cached
    """
    webhook_type = payload.get("type")
    data = payload.get("data", {})
    conversation_id = data.get("conversation_id")
    
    if not conversation_id:
        logger.warning("No conversation_id found in webhook payload")
        return None
    
    # Sanitize conversation_id
    conversation_id = sanitize_filename(conversation_id)
    
    # Use quarantine if not validated
    use_quarantine = not validated
    
    if webhook_type == "post_call_transcription":
        # Extract caller phone number
        caller_phone = extract_caller_phone_from_payload(payload)
        if caller_phone:
            caller_phone = sanitize_filename(caller_phone)
        
        # Save transcription webhook
        file_path = save_webhook_to_file(
            payload=payload,
            webhook_type="transcription",
            conversation_id=conversation_id,
            caller_phone=caller_phone,
            validated=validated,
            request_id=request_id,
            use_quarantine=use_quarantine
        )
        
        # Process cached audio webhook if exists (process even if caller_phone is None)
        if validated:
            audio_path = process_cached_audio_webhook(conversation_id, caller_phone)
            if audio_path:
                logger.info(f"Processed cached audio webhook: {audio_path}")
            else:
                logger.warning(f"No cached audio webhook found for conversation {conversation_id}. Audio webhook may not have been received, expired from cache, or failed to cache.")
        
        # Move from quarantine if validated
        if validated and use_quarantine:
            moved_path = move_file_from_quarantine(file_path, validated=True)
            if moved_path:
                file_path = moved_path
        
        return file_path
    
    elif webhook_type == "post_call_audio":
        # Decode base64 audio data
        full_audio = data.get("full_audio")
        if not full_audio:
            logger.warning("No full_audio found in audio webhook payload")
            return None
        
        try:
            audio_data = base64.b64decode(full_audio)
            
            # Check if transcription already exists (audio webhook arrived after transcription)
            transcription_file = None
            # Try to find transcription file in webhook storage
            base_path = settings.webhook_storage_path
            # Search in all subdirectories for transcription file
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    if file.startswith(f"{conversation_id}_transcription.json"):
                        transcription_file = os.path.join(root, file)
                        break
                if transcription_file:
                    break
            
            if transcription_file and os.path.exists(transcription_file):
                # Transcription already exists, process audio immediately
                logger.info(f"Transcription file already exists for conversation {conversation_id}, processing audio immediately")
                
                # Load transcription to extract caller phone
                try:
                    with open(transcription_file, 'r') as f:
                        transcription_payload = json.load(f)
                    caller_phone = extract_caller_phone_from_payload(transcription_payload)
                    if caller_phone:
                        caller_phone = sanitize_filename(caller_phone)
                        logger.info(f"Extracted caller phone from transcription: {caller_phone}")
                    else:
                        logger.warning(f"Could not extract caller phone from transcription file for conversation {conversation_id}")
                except Exception as e:
                    logger.error(f"Error loading transcription file to extract caller phone: {e}", exc_info=True)
                    caller_phone = None
                
                # Save audio file immediately
                audio_path = save_webhook_to_file(
                    payload=None,
                    webhook_type="audio",
                    conversation_id=conversation_id,
                    caller_phone=caller_phone,
                    audio_data=audio_data,
                    validated=validated,
                    request_id=request_id,
                    use_quarantine=use_quarantine
                )
                logger.info(f"Saved audio file immediately (transcription already exists): {audio_path}")
                return audio_path
            else:
                # Cache audio webhook until transcription arrives
                cache_audio_webhook(conversation_id, audio_data)
                logger.info(f"Cached audio webhook for conversation {conversation_id}, waiting for transcription")
                return None
        except Exception as e:
            logger.error(f"Error decoding audio webhook: {e}")
            return None
    
    elif webhook_type == "call_initiation_failure":
        # Extract agent_id from payload (failures don't have phone numbers)
        agent_id = data.get("agent_id")
        if agent_id:
            agent_id = sanitize_filename(agent_id)
        
        # Check for audio data in failure payload (unlikely but handle if present)
        full_audio = data.get("full_audio")
        audio_data = None
        if full_audio:
            try:
                audio_data = base64.b64decode(full_audio)
                logger.info(f"Found audio data in failure webhook for conversation {conversation_id}")
            except Exception as e:
                logger.error(f"Error decoding audio from failure webhook: {e}")
        
        # Save failure JSON
        failure_path = save_webhook_to_file(
            payload=payload,
            webhook_type="failure",
            conversation_id=conversation_id,
            agent_id=agent_id,
            validated=validated,
            request_id=request_id,
            use_quarantine=use_quarantine
        )
        
        # Save audio if present
        if audio_data:
            audio_path = save_webhook_to_file(
                payload=None,
                webhook_type="audio",
                conversation_id=conversation_id,
                agent_id=agent_id,
                audio_data=audio_data,
                validated=validated,
                request_id=request_id,
                use_quarantine=use_quarantine
            )
            logger.info(f"Saved audio from failure webhook: {audio_path}")
        
        # Move from quarantine if validated
        if validated and use_quarantine:
            moved_path = move_file_from_quarantine(failure_path, validated=True)
            if moved_path:
                failure_path = moved_path
        
        return failure_path
    
    else:
        logger.warning(f"Unknown webhook type: {webhook_type}")
        return None


def cleanup_old_files(directory: str, retention_days: int) -> Tuple[int, int]:
    """
    Clean up old files beyond retention period.
    
    Args:
        directory: Directory to clean up
        retention_days: Number of days to retain files
        
    Returns:
        Tuple of (files_deleted, bytes_freed)
    """
    if not os.path.exists(directory):
        return 0, 0
    
    cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
    files_deleted = 0
    bytes_freed = 0
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    # Check file modification time
                    mtime = os.path.getmtime(file_path)
                    if mtime < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_deleted += 1
                        bytes_freed += file_size
                        
                        # Also remove metadata file if exists
                        metadata_path = file_path + ".metadata.json"
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    if files_deleted > 0:
        logger.info(f"Cleaned up {files_deleted} old files ({bytes_freed / 1024 / 1024:.2f} MB) from {directory}")
    
    return files_deleted, bytes_freed


def cleanup_quarantine_files(quarantine_days: int = 7) -> Tuple[int, int]:
    """
    Clean up old files from quarantine directory.
    
    Args:
        quarantine_days: Number of days to retain quarantine files
        
    Returns:
        Tuple of (files_deleted, bytes_freed)
    """
    return cleanup_old_files(settings.webhook_quarantine_path, quarantine_days)


def cleanup_webhook_files() -> Tuple[int, int]:
    """
    Clean up old webhook files beyond retention period.
    
    Returns:
        Tuple of (files_deleted, bytes_freed)
    """
    return cleanup_old_files(settings.webhook_storage_path, settings.webhook_retention_days)

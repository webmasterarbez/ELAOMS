"""Configuration settings for ELAOMS."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # OpenMemory Configuration
    openmemory_url: str = "http://localhost:8080"
    openmemory_api_key: str
    
    # Eleven Labs Configuration
    elevenlabs_api_key: str
    elevenlabs_post_call_hmac_key: str  # HMAC key for post-call webhook signature validation
    elevenlabs_client_data_workspace_secret: Optional[str] = None  # Secret for client-data and search-data webhooks (X-Api-Key header)
    
    # ngrok Configuration (optional)
    ngrok_auth_token: Optional[str] = None
    
    # Webhook Storage Configuration
    webhook_storage_path: str = "data/webhooks"
    webhook_quarantine_path: str = "data/webhooks/quarantine"
    max_webhook_payload_size: int = 10 * 1024 * 1024  # 10MB in bytes (default for all types)
    max_transcription_payload_size: int = 10 * 1024 * 1024  # 10MB for transcription
    max_audio_payload_size: int = 50 * 1024 * 1024  # 50MB for audio (larger due to base64 encoding)
    max_failure_payload_size: int = 5 * 1024 * 1024  # 5MB for failure webhooks
    audio_cache_ttl: int = 3600  # 1 hour in seconds
    webhook_retention_days: int = 30  # Days to retain webhook files
    max_retries: int = 3  # Maximum retry attempts for API calls
    webhook_rate_limit: Optional[int] = None  # Rate limit per minute (None = no limit)
    webhook_rate_limit_per_user_agent: Optional[int] = None  # Rate limit per user agent
    webhook_rate_limit_per_api_key: Optional[int] = None  # Rate limit per API key
    cleanup_frequency_requests: int = 100  # Run cleanup every N requests
    cleanup_frequency_seconds: int = 3600  # Run cleanup every N seconds (alternative)
    anomaly_detection_enabled: bool = True  # Enable anomaly detection
    anomaly_failure_threshold: int = 5  # Number of validation failures before alerting
    anomaly_window_seconds: int = 300  # Time window for anomaly detection (5 minutes)
    alert_on_quarantine_failures: bool = True  # Alert when quarantine save fails
    redis_url: Optional[str] = None  # Redis URL for distributed caching (None = use in-memory)
    redis_ttl: int = 3600  # Redis TTL in seconds (default: 1 hour)
    file_permissions_mode: int = 0o600  # File permissions (read/write for owner only)
    enable_encryption_at_rest: bool = False  # Enable encryption at rest (requires cryptography)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()


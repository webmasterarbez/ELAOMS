"""Anomaly detection and alerting utilities for webhook security."""
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)

# Track validation failures per IP
_validation_failures: Dict[str, List[float]] = defaultdict(list)

# Track rate limit hits
_rate_limit_hits: Dict[str, List[float]] = defaultdict(list)

# Track quarantine failures
_quarantine_failures: List[Tuple[float, str, str]] = []  # (timestamp, request_id, error)


def record_validation_failure(client_ip: Optional[str], request_id: str) -> bool:
    """
    Record a validation failure and check for anomalies.
    
    Args:
        client_ip: Client IP address
        request_id: Request ID
        
    Returns:
        True if anomaly detected, False otherwise
    """
    if not settings.anomaly_detection_enabled:
        return False
    
    if not client_ip:
        return False
    
    current_time = time.time()
    window_start = current_time - settings.anomaly_window_seconds
    
    # Clean old entries
    _validation_failures[client_ip] = [
        t for t in _validation_failures[client_ip] if t > window_start
    ]
    
    # Add current failure
    _validation_failures[client_ip].append(current_time)
    
    # Check for anomaly
    failure_count = len(_validation_failures[client_ip])
    if failure_count >= settings.anomaly_failure_threshold:
        logger.warning(
            f"Anomaly detected: {failure_count} validation failures from {client_ip} in {settings.anomaly_window_seconds}s",
            extra={
                "client_ip": client_ip,
                "failure_count": failure_count,
                "window_seconds": settings.anomaly_window_seconds,
                "request_id": request_id,
                "anomaly_type": "validation_failure_spike"
            }
        )
        return True
    
    return False


def record_rate_limit_hit(client_ip: Optional[str], request_id: str) -> None:
    """
    Record a rate limit hit.
    
    Args:
        client_ip: Client IP address
        request_id: Request ID
    """
    if not client_ip:
        return
    
    current_time = time.time()
    window_start = current_time - 60  # 1 minute window
    
    # Clean old entries
    _rate_limit_hits[client_ip] = [
        t for t in _rate_limit_hits[client_ip] if t > window_start
    ]
    
    # Add current hit
    _rate_limit_hits[client_ip].append(current_time)
    
    # Check for spike in rate limit hits
    hit_count = len(_rate_limit_hits[client_ip])
    if hit_count >= 10:  # Alert if 10+ rate limit hits in 1 minute
        logger.warning(
            f"Rate limit spike detected: {hit_count} rate limit hits from {client_ip} in 1 minute",
            extra={
                "client_ip": client_ip,
                "hit_count": hit_count,
                "request_id": request_id,
                "anomaly_type": "rate_limit_spike"
            }
        )


def record_quarantine_failure(request_id: str, error: str) -> None:
    """
    Record a quarantine save failure.
    
    Args:
        request_id: Request ID
        error: Error message
    """
    if not settings.alert_on_quarantine_failures:
        return
    
    current_time = time.time()
    _quarantine_failures.append((current_time, request_id, error))
    
    # Clean old entries (keep last 100)
    if len(_quarantine_failures) > 100:
        _quarantine_failures[:] = _quarantine_failures[-100:]
    
    # Alert if multiple failures in short time
    recent_failures = [
        (t, rid, err) for t, rid, err in _quarantine_failures
        if (current_time - t) < 300  # Last 5 minutes
    ]
    
    if len(recent_failures) >= 5:
        logger.error(
            f"Quarantine failure spike: {len(recent_failures)} quarantine save failures in last 5 minutes",
            extra={
                "failure_count": len(recent_failures),
                "recent_failures": recent_failures[-5:],
                "anomaly_type": "quarantine_failure_spike"
            }
        )


def get_anomaly_stats() -> Dict[str, Any]:
    """
    Get current anomaly detection statistics.
    
    Returns:
        Dictionary with anomaly statistics
    """
    current_time = time.time()
    window_start = current_time - settings.anomaly_window_seconds
    
    # Count validation failures per IP
    ip_failures = {
        ip: len([t for t in failures if t > window_start])
        for ip, failures in _validation_failures.items()
    }
    
    # Count rate limit hits per IP
    rate_limit_window = current_time - 60
    ip_rate_limits = {
        ip: len([t for t in hits if t > rate_limit_window])
        for ip, hits in _rate_limit_hits.items()
    }
    
    # Count recent quarantine failures
    quarantine_window = current_time - 300
    recent_quarantine_failures = len([
        (t, rid, err) for t, rid, err in _quarantine_failures
        if t > quarantine_window
    ])
    
    return {
        "validation_failures": ip_failures,
        "rate_limit_hits": ip_rate_limits,
        "recent_quarantine_failures": recent_quarantine_failures,
        "anomaly_detection_enabled": settings.anomaly_detection_enabled
    }


def should_throttle_ip(client_ip: Optional[str]) -> bool:
    """
    Check if an IP should be throttled due to anomalies.
    
    Args:
        client_ip: Client IP address
        
    Returns:
        True if IP should be throttled, False otherwise
    """
    if not settings.anomaly_detection_enabled or not client_ip:
        return False
    
    current_time = time.time()
    window_start = current_time - settings.anomaly_window_seconds
    
    failures = _validation_failures.get(client_ip, [])
    recent_failures = [t for t in failures if t > window_start]
    
    # Throttle if exceeds threshold
    return len(recent_failures) >= settings.anomaly_failure_threshold


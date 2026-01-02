"""Input validation and security checks for AgentBill SDK"""
import re
from typing import Any, Dict
from urllib.parse import urlparse


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


def validate_api_key(api_key: str) -> None:
    """
    Validates API key format.
    Must be non-empty alphanumeric with hyphens/underscores, 20-100 chars.
    """
    if not api_key or not isinstance(api_key, str):
        raise ValidationError("API key is required and must be a string")
    
    if len(api_key) < 20 or len(api_key) > 100:
        raise ValidationError("API key must be between 20 and 100 characters")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        raise ValidationError("API key contains invalid characters")


def validate_base_url(url: str) -> str:
    """
    Validates and sanitizes base URL.
    Prevents SSRF attacks by only allowing HTTPS and specific domains.
    """
    if not url or not isinstance(url, str):
        raise ValidationError("Base URL is required and must be a string")
    
    # Remove trailing slashes
    url = url.rstrip('/')
    
    # Validate URL format
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValidationError("Invalid base URL format")
    
    # Only allow HTTPS (or HTTP for localhost in development)
    if parsed.scheme not in ('https', 'http'):
        raise ValidationError("Base URL must use HTTPS protocol")
    
    if parsed.scheme == 'http' and not any(
        h in parsed.netloc.lower() 
        for h in ('localhost', '127.0.0.1')
    ):
        raise ValidationError("HTTP only allowed for localhost")
    
    # Prevent SSRF to internal networks
    hostname = parsed.hostname or ''
    blocked_patterns = [
        r'^10\.',
        r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
        r'^192\.168\.',
        r'^169\.254\.',
        r'^127\.',
        r'^0\.',
        r'^localhost$',
        r'^metadata',
        r'^169\.254\.169\.254$',
    ]
    
    if 'localhost' not in url and '127.0.0.1' not in url:
        for pattern in blocked_patterns:
            if re.match(pattern, hostname, re.IGNORECASE):
                raise ValidationError("Base URL points to internal/private network")
    
    return url


def validate_customer_id(customer_id: str) -> None:
    """
    Validates customer ID.
    Must be alphanumeric with limited special chars, max 255 chars.
    """
    if not isinstance(customer_id, str):
        raise ValidationError("Customer ID must be a string")
    
    if len(customer_id) == 0 or len(customer_id) > 255:
        raise ValidationError("Customer ID must be between 1 and 255 characters")
    
    if not re.match(r'^[a-zA-Z0-9_.-]+$', customer_id):
        raise ValidationError("Customer ID contains invalid characters")


def validate_event_name(event_name: str) -> None:
    """
    Validates event name for custom signals.
    Must be alphanumeric with underscores, max 100 chars.
    """
    if not event_name or not isinstance(event_name, str):
        raise ValidationError("Event name is required and must be a string")
    
    if len(event_name) == 0 or len(event_name) > 100:
        raise ValidationError("Event name must be between 1 and 100 characters")
    
    if not re.match(r'^[a-z0-9_]+$', event_name):
        raise ValidationError("Event name must be lowercase alphanumeric with underscores")


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """
    Validates metadata object.
    Prevents injection and limits size.
    """
    if not isinstance(metadata, dict):
        raise ValidationError("Metadata must be a dictionary")
    
    # Limit number of keys
    if len(metadata) > 50:
        raise ValidationError("Metadata cannot have more than 50 keys")
    
    # Validate each key-value pair
    import json
    for key, value in metadata.items():
        if not isinstance(key, str) or len(key) == 0 or len(key) > 100:
            raise ValidationError("Metadata keys must be strings between 1 and 100 characters")
        
        # Value size limit
        value_str = json.dumps(value)
        if len(value_str) > 10000:
            raise ValidationError(f"Metadata value for key '{key}' exceeds 10KB limit")
    
    # Total size limit
    total_size = len(json.dumps(metadata))
    if total_size > 100000:
        raise ValidationError("Total metadata size exceeds 100KB limit")


def validate_revenue(revenue: float) -> None:
    """Validates revenue amount"""
    if not isinstance(revenue, (int, float)):
        raise ValidationError("Revenue must be a number")
    
    if revenue < 0:
        raise ValidationError("Revenue cannot be negative")
    
    if not isinstance(revenue, (int, float)) or revenue != revenue:  # NaN check
        raise ValidationError("Revenue must be a valid number")

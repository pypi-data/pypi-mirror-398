"""Utility functions for the Mindzie API client."""

import json
import time
import hashlib
import mimetypes
import random
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def parse_datetime(dt_string: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not dt_string:
        return None
    try:
        # Handle different datetime formats
        if 'T' in dt_string:
            if dt_string.endswith('Z'):
                return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            return datetime.fromisoformat(dt_string)
        return datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        logger.warning(f"Failed to parse datetime: {dt_string}")
        return None


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """Convert datetime to ISO string format."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def validate_guid(guid_string: str) -> bool:
    """Validate if string is a valid GUID."""
    try:
        # Basic GUID format validation
        parts = guid_string.split('-')
        if len(parts) != 5:
            return False
        if len(parts[0]) != 8 or len(parts[1]) != 4 or len(parts[2]) != 4:
            return False
        if len(parts[3]) != 4 or len(parts[4]) != 12:
            return False
        # Check if all characters are hexadecimal
        int(guid_string.replace('-', ''), 16)
        return True
    except (ValueError, AttributeError):
        return False


def calculate_retry_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """Calculate exponential backoff delay for retries with random jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    # Add random jitter to prevent thundering herd (±10% of delay)
    jitter = delay * 0.1 * (random.random() * 2 - 1)  # Random between -0.1 and +0.1
    return max(0, delay + jitter)


def get_file_mime_type(file_path: Union[str, Path]) -> str:
    """Get MIME type of a file."""
    file_path = Path(file_path)
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'


def calculate_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Calculate hash of a file."""
    file_path = Path(file_path)
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def paginate_results(
    items: List[Any],
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    """Paginate a list of items."""
    total_count = len(items)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    return {
        "items": items[start_index:end_index],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


def build_query_params(
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """Build query parameters for API requests."""
    params = {}
    if page is not None:
        params['page'] = page
    if page_size is not None:
        params['pageSize'] = page_size
    
    # Add additional parameters
    for key, value in kwargs.items():
        if value is not None:
            if isinstance(value, bool):
                params[key] = str(value).lower()
            elif isinstance(value, datetime):
                params[key] = to_iso_string(value)
            else:
                params[key] = value
    
    return params


def parse_error_response(response_text: str) -> Dict[str, Any]:
    """Parse error response from API."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {
            "error": response_text or "Unknown error",
            "details": None
        }


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary value."""
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result
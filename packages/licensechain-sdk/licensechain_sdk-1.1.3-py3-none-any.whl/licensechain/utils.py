import re
import uuid
import time
import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(pattern, email))


def validate_license_key(license_key: str) -> bool:
    """Validate license key format."""
    if not license_key or len(license_key) != 32:
        return False
    return bool(re.match(r'^[A-Z0-9]+$', license_key))


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def validate_amount(amount: Union[int, float]) -> bool:
    """Validate amount is positive."""
    return isinstance(amount, (int, float)) and amount > 0 and not (isinstance(amount, float) and amount != amount)


def validate_currency(currency: str) -> bool:
    """Validate currency code."""
    valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY', 'CHF', 'CNY']
    return currency.upper() in valid_currencies


def validate_status(status: str, allowed_statuses: List[str]) -> bool:
    """Validate status against allowed values."""
    return status in allowed_statuses


def sanitize_input(input_string: str) -> str:
    """Sanitize input by escaping HTML characters."""
    if not isinstance(input_string, str):
        return str(input_string)
    
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
    }
    
    for char, replacement in replacements.items():
        input_string = input_string.replace(char, replacement)
    
    return input_string


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize metadata dictionary."""
    if not isinstance(metadata, dict):
        return metadata
    
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_metadata(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_input(item) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized


def generate_license_key() -> str:
    """Generate a random license key."""
    import random
    import string
    
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(32))


def generate_uuid() -> str:
    """Generate a random UUID v4."""
    return str(uuid.uuid4())


def format_timestamp(timestamp: Union[int, float]) -> str:
    """Format timestamp to ISO 8601 string."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.isoformat()


def parse_timestamp(timestamp: str) -> float:
    """Parse ISO 8601 timestamp string."""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.timestamp()
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {e}")


def validate_pagination(page: Optional[int], limit: Optional[int]) -> tuple[int, int]:
    """Validate pagination parameters."""
    page = max(page or 1, 1)
    limit = min(max(limit or 10, 1), 100)
    return page, limit


def validate_date_range(start_date: str, end_date: str) -> None:
    """Validate date range."""
    start_time = parse_timestamp(start_date)
    end_time = parse_timestamp(end_date)
    
    if start_time > end_time:
        raise ValueError("Start date must be before or equal to end date")


def create_webhook_signature(payload: str, secret: str) -> str:
    """Create webhook signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected_signature = create_webhook_signature(payload, secret)
    return hmac.compare_digest(signature, expected_signature)


def retry_with_backoff(max_retries: int = 3, initial_delay: float = 1.0):
    """Decorator for retrying with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    time.sleep(delay)
                    delay *= 2
            return None
        return wrapper
    return decorator


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format."""
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    threshold = 1024
    
    if bytes_value < threshold:
        return f"{bytes_value} B"
    
    size = float(bytes_value)
    unit_index = 0
    
    while size >= threshold and unit_index < len(units) - 1:
        size /= threshold
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: Union[int, float]) -> str:
    """Format duration to human readable format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def capitalize_first(text: str) -> str:
    """Capitalize the first letter of a string."""
    if not text:
        return text
    return text[0].upper() + text[1:].lower()


def to_snake_case(text: str) -> str:
    """Convert string to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_pascal_case(text: str) -> str:
    """Convert string to PascalCase."""
    return ''.join(word.capitalize() for word in text.split('_'))


def truncate_string(text: str, max_length: int) -> str:
    """Truncate string to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'


def remove_special_chars(text: str) -> str:
    """Remove special characters from string."""
    return re.sub(r'[^a-zA-Z0-9\s]', '', text)


def slugify(text: str) -> str:
    """Create a slug from string."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def validate_not_empty(value: str, field_name: str) -> None:
    """Validate that string is not empty."""
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")


def validate_positive(value: Union[int, float], field_name: str) -> None:
    """Validate that number is positive."""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float], field_name: str) -> None:
    """Validate that number is within range."""
    if value < min_val or value > max_val:
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}")


def json_serialize(obj: Any) -> str:
    """Serialize object to JSON string."""
    return json.dumps(obj, default=str, ensure_ascii=False)


def json_deserialize(json_string: str) -> Any:
    """Deserialize JSON string to object."""
    return json.loads(json_string)


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Unflatten dictionary with nested keys."""
    result = {}
    for key, value in d.items():
        keys = key.split(sep)
        current = result
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    return result

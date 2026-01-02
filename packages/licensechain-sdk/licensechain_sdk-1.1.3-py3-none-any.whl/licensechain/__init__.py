"""
LicenseChain Python SDK

A comprehensive Python SDK for the LicenseChain API.
"""

from .simple_client import Client
from .exceptions import (
    LicenseChainError, NetworkError, ApiError, ValidationError,
    AuthenticationError, NotFoundError, RateLimitError, TimeoutError,
    SerializationError, DeserializationError, ConfigurationError, UnknownError
)
from .webhook_handler import WebhookHandler, WebhookEvents
from .utils import (
    validate_email, validate_license_key, validate_uuid, validate_amount,
    validate_currency, validate_status, sanitize_input, sanitize_metadata,
    generate_license_key, generate_uuid, format_timestamp, parse_timestamp,
    validate_pagination, validate_date_range, create_webhook_signature,
    verify_webhook_signature, retry_with_backoff, format_bytes, format_duration,
    capitalize_first, to_snake_case, to_pascal_case, truncate_string,
    remove_special_chars, slugify, validate_not_empty, validate_positive,
    validate_range, json_serialize, json_deserialize, deep_merge,
    chunk_list, flatten_dict, unflatten_dict
)

__version__ = '1.0.0'
__author__ = 'LicenseChain'
__email__ = 'support@licensechain.app'

__all__ = [
    'Client',
    'WebhookHandler',
    'WebhookEvents',
    'LicenseChainError',
    'NetworkError',
    'ApiError',
    'ValidationError',
    'AuthenticationError',
    'NotFoundError',
    'RateLimitError',
    'TimeoutError',
    'SerializationError',
    'DeserializationError',
    'ConfigurationError',
    'UnknownError',
    'validate_email',
    'validate_license_key',
    'validate_uuid',
    'validate_amount',
    'validate_currency',
    'validate_status',
    'sanitize_input',
    'sanitize_metadata',
    'generate_license_key',
    'generate_uuid',
    'format_timestamp',
    'parse_timestamp',
    'validate_pagination',
    'validate_date_range',
    'create_webhook_signature',
    'verify_webhook_signature',
    'retry_with_backoff',
    'format_bytes',
    'format_duration',
    'capitalize_first',
    'to_snake_case',
    'to_pascal_case',
    'truncate_string',
    'remove_special_chars',
    'slugify',
    'validate_not_empty',
    'validate_positive',
    'validate_range',
    'json_serialize',
    'json_deserialize',
    'deep_merge',
    'chunk_list',
    'flatten_dict',
    'unflatten_dict'
]
import requests
import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlencode

from .exceptions import (
    NetworkError, ApiError, ValidationError, AuthenticationError,
    NotFoundError, RateLimitError, TimeoutError, SerializationError,
    DeserializationError, ConfigurationError, UnknownError
)
from .utils import retry_with_backoff, json_serialize, json_deserialize


class ApiClient:
    """HTTP client for LicenseChain API."""
    
    def __init__(self, api_key: str, base_url: str = 'https://api.licensechain.app', 
                 timeout: int = 30, retries: int = 3):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Setup session with default headers."""
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-API-Version': '1.0',
            'X-Platform': 'python-sdk',
            'User-Agent': 'LicenseChain-Python-SDK/1.0.0'
        })
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request('PUT', endpoint, data=data)
    
    def delete(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request('DELETE', endpoint, data=data)
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict[str, Any]] = None, 
                     params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        # Ensure endpoint starts with /v1 prefix
        if not endpoint.startswith('/v1/'):
            if endpoint.startswith('/'):
                endpoint = f'/v1{endpoint}'
            else:
                endpoint = f'/v1/{endpoint}'
        
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=self.timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, timeout=self.timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, json=data, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return self._handle_response(response)
            
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request error: {e}")
        except Exception as e:
            raise UnknownError(f"Unexpected error: {e}")
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle HTTP response."""
        try:
            if response.status_code in range(200, 300):
                if response.content:
                    return response.json()
                return {}
            elif response.status_code == 400:
                error_msg = self._extract_error_message(response)
                raise ValidationError(f"Bad Request: {error_msg}")
            elif response.status_code == 401:
                error_msg = self._extract_error_message(response)
                raise AuthenticationError(f"Unauthorized: {error_msg}")
            elif response.status_code == 403:
                error_msg = self._extract_error_message(response)
                raise AuthenticationError(f"Forbidden: {error_msg}")
            elif response.status_code == 404:
                error_msg = self._extract_error_message(response)
                raise NotFoundError(f"Not Found: {error_msg}")
            elif response.status_code == 429:
                error_msg = self._extract_error_message(response)
                raise RateLimitError(f"Rate Limited: {error_msg}")
            elif response.status_code in range(500, 600):
                error_msg = self._extract_error_message(response)
                raise ApiError(f"Server Error: {error_msg}")
            else:
                error_msg = self._extract_error_message(response)
                raise UnknownError(f"Unexpected response: {response.status_code} {error_msg}")
        except json.JSONDecodeError as e:
            raise DeserializationError(f"Failed to parse JSON response: {e}")
    
    def _extract_error_message(self, response: requests.Response) -> str:
        """Extract error message from response."""
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get('error', data.get('message', response.text))
            return response.text
        except (json.JSONDecodeError, AttributeError):
            return response.text
    
    def ping(self) -> Dict[str, Any]:
        """Ping the API."""
        return self.get('/v1/ping')
    
    def health(self) -> Dict[str, Any]:
        """Check API health."""
        return self.get('/v1/health')
    
    def close(self):
        """Close the session."""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

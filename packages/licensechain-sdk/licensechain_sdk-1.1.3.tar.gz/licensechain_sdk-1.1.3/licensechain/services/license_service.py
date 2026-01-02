from typing import Any, Dict, List, Optional

from ..exceptions import ValidationError
from ..utils import validate_uuid, validate_not_empty, sanitize_metadata, validate_pagination
from ..models import License, LicenseStats


class LicenseService:
    """Service for license management."""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def create(self, user_id: str, product_id: str, metadata: Optional[Dict[str, Any]] = None) -> License:
        """Create a new license."""
        self._validate_required_params(user_id, product_id)
        
        data = {
            'user_id': user_id,
            'product_id': product_id,
            'metadata': sanitize_metadata(metadata or {})
        }
        
        response = self.api_client.post('/licenses', data)
        return License(**response['data'])
    
    def get(self, license_id: str) -> License:
        """Get a license by ID."""
        self._validate_uuid(license_id, 'license_id')
        
        response = self.api_client.get(f'/licenses/{license_id}')
        return License(**response['data'])
    
    def update(self, license_id: str, updates: Dict[str, Any]) -> License:
        """Update a license."""
        self._validate_uuid(license_id, 'license_id')
        
        response = self.api_client.put(f'/licenses/{license_id}', sanitize_metadata(updates))
        return License(**response['data'])
    
    def revoke(self, license_id: str) -> bool:
        """Revoke a license."""
        self._validate_uuid(license_id, 'license_id')
        
        self.api_client.delete(f'/licenses/{license_id}')
        return True
    
    def validate(self, license_key: str) -> bool:
        """Validate a license key."""
        validate_not_empty(license_key, 'license_key')
        
        # Use /licenses/verify endpoint with 'key' parameter to match API
        response = self.api_client.post('/licenses/verify', {'key': license_key})
        return response.get('valid', False)
    
    def list_user_licenses(self, user_id: str, page: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """List licenses for a user."""
        self._validate_uuid(user_id, 'user_id')
        page, limit = validate_pagination(page, limit)
        
        response = self.api_client.get('/licenses', {
            'user_id': user_id,
            'page': page,
            'limit': limit
        })
        
        return {
            'data': [License(**license) for license in response['data']],
            'total': response['total'],
            'page': response['page'],
            'limit': response['limit']
        }
    
    def stats(self) -> LicenseStats:
        """Get license statistics."""
        response = self.api_client.get('/licenses/stats')
        return LicenseStats(**response['data'])
    
    def _validate_required_params(self, user_id: str, product_id: str) -> None:
        """Validate required parameters."""
        validate_not_empty(user_id, 'user_id')
        validate_not_empty(product_id, 'product_id')
    
    def _validate_uuid(self, id_value: str, field_name: str) -> None:
        """Validate UUID format."""
        validate_not_empty(id_value, field_name)
        if not validate_uuid(id_value):
            raise ValidationError(f"Invalid {field_name} format")

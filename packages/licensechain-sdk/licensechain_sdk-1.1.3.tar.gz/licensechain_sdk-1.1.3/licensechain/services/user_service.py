from typing import Any, Dict, List, Optional

from ..exceptions import ValidationError
from ..utils import validate_uuid, validate_not_empty, validate_email, sanitize_metadata, validate_pagination
from ..models import User, UserStats


class UserService:
    """Service for user management."""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def create(self, email: str, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> User:
        """Create a new user."""
        self._validate_email(email)
        
        data = {
            'email': email,
            'name': name,
            'metadata': sanitize_metadata(metadata or {})
        }
        
        response = self.api_client.post('/users', data)
        return User(**response['data'])
    
    def get(self, user_id: str) -> User:
        """Get a user by ID."""
        self._validate_uuid(user_id, 'user_id')
        
        response = self.api_client.get(f'/users/{user_id}')
        return User(**response['data'])
    
    def update(self, user_id: str, updates: Dict[str, Any]) -> User:
        """Update a user."""
        self._validate_uuid(user_id, 'user_id')
        
        response = self.api_client.put(f'/users/{user_id}', sanitize_metadata(updates))
        return User(**response['data'])
    
    def delete(self, user_id: str) -> bool:
        """Delete a user."""
        self._validate_uuid(user_id, 'user_id')
        
        self.api_client.delete(f'/users/{user_id}')
        return True
    
    def list(self, page: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """List users."""
        page, limit = validate_pagination(page, limit)
        
        response = self.api_client.get('/users', {
            'page': page,
            'limit': limit
        })
        
        return {
            'data': [User(**user) for user in response['data']],
            'total': response['total'],
            'page': response['page'],
            'limit': response['limit']
        }
    
    def stats(self) -> UserStats:
        """Get user statistics."""
        response = self.api_client.get('/users/stats')
        return UserStats(**response['data'])
    
    def _validate_email(self, email: str) -> None:
        """Validate email format."""
        validate_not_empty(email, 'email')
        if not validate_email(email):
            raise ValidationError('Invalid email format')
    
    def _validate_uuid(self, id_value: str, field_name: str) -> None:
        """Validate UUID format."""
        validate_not_empty(id_value, field_name)
        if not validate_uuid(id_value):
            raise ValidationError(f"Invalid {field_name} format")

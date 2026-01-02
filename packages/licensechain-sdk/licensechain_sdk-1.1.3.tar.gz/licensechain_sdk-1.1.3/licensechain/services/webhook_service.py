from typing import Any, Dict, List, Optional

from ..exceptions import ValidationError
from ..utils import validate_uuid, validate_not_empty, sanitize_metadata
from ..models import Webhook


class WebhookService:
    """Service for webhook management."""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def create(self, url: str, events: List[str], secret: Optional[str] = None) -> Webhook:
        """Create a new webhook."""
        self._validate_webhook_params(url, events)
        
        data = {
            'url': url,
            'events': events,
            'secret': secret
        }
        
        response = self.api_client.post('/webhooks', data)
        return Webhook(**response['data'])
    
    def get(self, webhook_id: str) -> Webhook:
        """Get a webhook by ID."""
        self._validate_uuid(webhook_id, 'webhook_id')
        
        response = self.api_client.get(f'/webhooks/{webhook_id}')
        return Webhook(**response['data'])
    
    def update(self, webhook_id: str, updates: Dict[str, Any]) -> Webhook:
        """Update a webhook."""
        self._validate_uuid(webhook_id, 'webhook_id')
        
        response = self.api_client.put(f'/webhooks/{webhook_id}', sanitize_metadata(updates))
        return Webhook(**response['data'])
    
    def delete(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        self._validate_uuid(webhook_id, 'webhook_id')
        
        self.api_client.delete(f'/webhooks/{webhook_id}')
        return True
    
    def list(self) -> List[Webhook]:
        """List webhooks."""
        response = self.api_client.get('/webhooks')
        return [Webhook(**webhook) for webhook in response['data']]
    
    def _validate_webhook_params(self, url: str, events: List[str]) -> None:
        """Validate webhook parameters."""
        validate_not_empty(url, 'url')
        if not isinstance(events, list):
            raise ValidationError('Events must be a list')
        if not events:
            raise ValidationError('Events cannot be empty')
    
    def _validate_uuid(self, id_value: str, field_name: str) -> None:
        """Validate UUID format."""
        validate_not_empty(id_value, field_name)
        if not validate_uuid(id_value):
            raise ValidationError(f"Invalid {field_name} format")

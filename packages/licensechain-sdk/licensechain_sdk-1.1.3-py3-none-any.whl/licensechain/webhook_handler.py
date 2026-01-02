import hmac
import hashlib
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .exceptions import ValidationError, AuthenticationError
from .utils import verify_webhook_signature, create_webhook_signature


class WebhookHandler:
    """Handler for processing webhook events."""
    
    def __init__(self, secret: str, tolerance: int = 300):
        self.secret = secret
        self.tolerance = tolerance  # seconds
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature."""
        return verify_webhook_signature(payload, signature, self.secret)
    
    def verify_timestamp(self, timestamp: str) -> None:
        """Verify webhook timestamp."""
        try:
            webhook_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            time_diff = abs((current_time - webhook_time).total_seconds())
            
            if time_diff > self.tolerance:
                raise ValidationError(f"Webhook timestamp too old: {time_diff} seconds")
        except ValueError as e:
            raise ValidationError(f"Invalid timestamp format: {e}")
    
    def verify_webhook(self, payload: str, signature: str, timestamp: str) -> None:
        """Verify complete webhook."""
        self.verify_timestamp(timestamp)
        
        if not self.verify_signature(payload, signature):
            raise AuthenticationError("Invalid webhook signature")
    
    def process_event(self, event_data: Dict[str, Any]) -> None:
        """Process webhook event."""
        payload = json.dumps(event_data.get('data', {}))
        self.verify_webhook(payload, event_data['signature'], event_data['timestamp'])
        
        event_type = event_data.get('type')
        
        if event_type == 'license.created':
            self._handle_license_created(event_data)
        elif event_type == 'license.updated':
            self._handle_license_updated(event_data)
        elif event_type == 'license.revoked':
            self._handle_license_revoked(event_data)
        elif event_type == 'license.expired':
            self._handle_license_expired(event_data)
        elif event_type == 'user.created':
            self._handle_user_created(event_data)
        elif event_type == 'user.updated':
            self._handle_user_updated(event_data)
        elif event_type == 'user.deleted':
            self._handle_user_deleted(event_data)
        elif event_type == 'product.created':
            self._handle_product_created(event_data)
        elif event_type == 'product.updated':
            self._handle_product_updated(event_data)
        elif event_type == 'product.deleted':
            self._handle_product_deleted(event_data)
        elif event_type == 'payment.completed':
            self._handle_payment_completed(event_data)
        elif event_type == 'payment.failed':
            self._handle_payment_failed(event_data)
        elif event_type == 'payment.refunded':
            self._handle_payment_refunded(event_data)
        else:
            print(f"Unknown webhook event type: {event_type}")
    
    def _handle_license_created(self, event_data: Dict[str, Any]) -> None:
        """Handle license created event."""
        print(f"License created: {event_data['id']}")
        # Add custom logic for license created event
    
    def _handle_license_updated(self, event_data: Dict[str, Any]) -> None:
        """Handle license updated event."""
        print(f"License updated: {event_data['id']}")
        # Add custom logic for license updated event
    
    def _handle_license_revoked(self, event_data: Dict[str, Any]) -> None:
        """Handle license revoked event."""
        print(f"License revoked: {event_data['id']}")
        # Add custom logic for license revoked event
    
    def _handle_license_expired(self, event_data: Dict[str, Any]) -> None:
        """Handle license expired event."""
        print(f"License expired: {event_data['id']}")
        # Add custom logic for license expired event
    
    def _handle_user_created(self, event_data: Dict[str, Any]) -> None:
        """Handle user created event."""
        print(f"User created: {event_data['id']}")
        # Add custom logic for user created event
    
    def _handle_user_updated(self, event_data: Dict[str, Any]) -> None:
        """Handle user updated event."""
        print(f"User updated: {event_data['id']}")
        # Add custom logic for user updated event
    
    def _handle_user_deleted(self, event_data: Dict[str, Any]) -> None:
        """Handle user deleted event."""
        print(f"User deleted: {event_data['id']}")
        # Add custom logic for user deleted event
    
    def _handle_product_created(self, event_data: Dict[str, Any]) -> None:
        """Handle product created event."""
        print(f"Product created: {event_data['id']}")
        # Add custom logic for product created event
    
    def _handle_product_updated(self, event_data: Dict[str, Any]) -> None:
        """Handle product updated event."""
        print(f"Product updated: {event_data['id']}")
        # Add custom logic for product updated event
    
    def _handle_product_deleted(self, event_data: Dict[str, Any]) -> None:
        """Handle product deleted event."""
        print(f"Product deleted: {event_data['id']}")
        # Add custom logic for product deleted event
    
    def _handle_payment_completed(self, event_data: Dict[str, Any]) -> None:
        """Handle payment completed event."""
        print(f"Payment completed: {event_data['id']}")
        # Add custom logic for payment completed event
    
    def _handle_payment_failed(self, event_data: Dict[str, Any]) -> None:
        """Handle payment failed event."""
        print(f"Payment failed: {event_data['id']}")
        # Add custom logic for payment failed event
    
    def _handle_payment_refunded(self, event_data: Dict[str, Any]) -> None:
        """Handle payment refunded event."""
        print(f"Payment refunded: {event_data['id']}")
        # Add custom logic for payment refunded event


class WebhookEvents:
    """Webhook event type constants."""
    
    LICENSE_CREATED = 'license.created'
    LICENSE_UPDATED = 'license.updated'
    LICENSE_REVOKED = 'license.revoked'
    LICENSE_EXPIRED = 'license.expired'
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'
    PRODUCT_CREATED = 'product.created'
    PRODUCT_UPDATED = 'product.updated'
    PRODUCT_DELETED = 'product.deleted'
    PAYMENT_COMPLETED = 'payment.completed'
    PAYMENT_FAILED = 'payment.failed'
    PAYMENT_REFUNDED = 'payment.refunded'


def create_outgoing_webhook_signature(payload: str, secret: str) -> str:
    """Create webhook signature for outgoing webhooks."""
    return create_webhook_signature(payload, secret)


def verify_incoming_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify incoming webhook signature."""
    return verify_webhook_signature(payload, signature, secret)

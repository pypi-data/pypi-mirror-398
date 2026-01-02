"""
LicenseChain Webhook Verifier

Secure webhook verification and handling functionality.
"""

import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timezone

from .exceptions import ValidationError


class WebhookVerifier:
    """
    Webhook verifier for secure webhook handling.
    
    This class provides methods for verifying webhook signatures
    and parsing webhook payloads securely.
    """

    def __init__(self, secret: str):
        """
        Initialize the webhook verifier.
        
        Args:
            secret: Webhook secret for signature verification
        """
        if not secret:
            raise ValueError("Webhook secret is required")
        self.secret = secret

    def verify_signature(
        self,
        payload: str,
        signature: str,
        algorithm: str = "sha256"
    ) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            algorithm: Signature algorithm (sha1, sha256, sha512)
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = self.generate_signature(payload, algorithm)
            return self._secure_compare(signature, expected_signature)
        except Exception:
            return False

    def parse_payload(
        self,
        payload: str,
        signature: str,
        algorithm: str = "sha256"
    ) -> Dict[str, Any]:
        """
        Parse and verify webhook payload.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            algorithm: Signature algorithm
            
        Returns:
            Parsed webhook data
            
        Raises:
            ValidationError: If signature is invalid or payload is malformed
        """
        if not self.verify_signature(payload, signature, algorithm):
            raise ValidationError("Invalid webhook signature")
        
        try:
            return json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON payload: {e}")

    def generate_signature(
        self, payload: str, algorithm: str = "sha256"
    ) -> str:
        """
        Generate signature for testing.
        
        Args:
            payload: Raw payload
            algorithm: Signature algorithm
            
        Returns:
            Generated signature
        """
        if algorithm.lower() == "sha1":
            digest = hashlib.sha1
        elif algorithm.lower() == "sha256":
            digest = hashlib.sha256
        elif algorithm.lower() == "sha512":
            digest = hashlib.sha512
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        signature = hmac.new(
            self.secret.encode("utf-8"),
            payload.encode("utf-8"),
            digest
        ).hexdigest()
        
        return f"{algorithm}={signature}"

    def verify_event_type(
        self, payload: Dict[str, Any], expected_type: str
    ) -> bool:
        """
        Verify webhook event type.
        
        Args:
            payload: Parsed webhook payload
            expected_type: Expected event type
            
        Returns:
            True if event type matches, False otherwise
        """
        event_type = payload.get("type") or payload.get("event")
        return event_type == expected_type

    def extract_event_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract event data from webhook payload.
        
        Args:
            payload: Parsed webhook payload
            
        Returns:
            Extracted event data
        """
        return {
            "id": payload.get("id"),
            "type": payload.get("type") or payload.get("event"),
            "created_at": payload.get("created_at"),
            "data": payload.get("data") or payload.get("object"),
        }

    def verify_timestamp(
        self, payload: Dict[str, Any], tolerance: int = 300
    ) -> bool:
        """
        Verify webhook timestamp (prevent replay attacks).
        
        Args:
            payload: Parsed webhook payload
            tolerance: Time tolerance in seconds (default: 5 minutes)
            
        Returns:
            True if timestamp is valid, False otherwise
        """
        timestamp = payload.get("timestamp") or payload.get("created_at")
        if not timestamp:
            return True
        
        try:
            event_time = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
            current_time = datetime.now(timezone.utc)
            return abs((current_time - event_time).total_seconds()) <= tolerance
        except (ValueError, TypeError):
            return False

    def _secure_compare(self, a: str, b: str) -> bool:
        """Securely compare two strings."""
        if not a or not b or len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a.encode(), b.encode()):
            result |= x ^ y
        return result == 0


class WebhookHandler:
    """
    Webhook event handler.
    
    This class provides a framework for handling webhook events
    with automatic routing to appropriate handler methods.
    """

    def __init__(self, secret: str):
        """
        Initialize the webhook handler.
        
        Args:
            secret: Webhook secret for verification
        """
        self.verifier = WebhookVerifier(secret)

    async def handle(
        self,
        payload: str,
        signature: str,
        algorithm: str = "sha256"
    ) -> Dict[str, Any]:
        """
        Handle webhook payload.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            algorithm: Signature algorithm
            
        Returns:
            Processing result
        """
        # Parse and verify the payload
        data = self.verifier.parse_payload(payload, signature, algorithm)
        
        # Verify timestamp to prevent replay attacks
        if not self.verifier.verify_timestamp(data):
            raise ValidationError("Webhook timestamp is too old")
        
        # Extract event information
        event_data = self.verifier.extract_event_data(data)
        
        # Route to appropriate handler
        return await self._handle_event(event_data)

    async def _handle_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route event to appropriate handler."""
        event_type = event_data.get("type")
        
        handler_map = {
            "license.created": self.handle_license_created,
            "license.updated": self.handle_license_updated,
            "license.revoked": self.handle_license_revoked,
            "license.expired": self.handle_license_expired,
            "license.validated": self.handle_license_validated,
            "app.created": self.handle_app_created,
            "app.updated": self.handle_app_updated,
            "app.deleted": self.handle_app_deleted,
            "user.created": self.handle_user_created,
            "user.updated": self.handle_user_updated,
        }
        
        handler = handler_map.get(event_type, self.handle_unknown_event)
        return await handler(event_data)

    # Event handlers - override in subclasses
    async def handle_license_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license created event."""
        return {"status": "processed", "event": "license.created"}

    async def handle_license_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license updated event."""
        return {"status": "processed", "event": "license.updated"}

    async def handle_license_revoked(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license revoked event."""
        return {"status": "processed", "event": "license.revoked"}

    async def handle_license_expired(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license expired event."""
        return {"status": "processed", "event": "license.expired"}

    async def handle_license_validated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle license validated event."""
        return {"status": "processed", "event": "license.validated"}

    async def handle_app_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app created event."""
        return {"status": "processed", "event": "app.created"}

    async def handle_app_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app updated event."""
        return {"status": "processed", "event": "app.updated"}

    async def handle_app_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle app deleted event."""
        return {"status": "processed", "event": "app.deleted"}

    async def handle_user_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user created event."""
        return {"status": "processed", "event": "user.created"}

    async def handle_user_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user updated event."""
        return {"status": "processed", "event": "user.updated"}

    async def handle_unknown_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown event type."""
        return {"status": "ignored", "event": event_data.get("type", "unknown")}

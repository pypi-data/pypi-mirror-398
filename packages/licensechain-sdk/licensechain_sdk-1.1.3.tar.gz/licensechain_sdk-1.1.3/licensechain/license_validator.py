"""
LicenseChain License Validator

Easy-to-use license validation functionality.
"""

import asyncio
from typing import Any, Dict, List, Optional

from .client import LicenseChainClient
from .exceptions import LicenseChainException
from .models import ValidationResult


class LicenseValidator:
    """
    License validator for easy license validation.
    
    This class provides a simplified interface for validating licenses
    without needing to directly interact with the API client.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.licensechain.app",
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the license validator.
        
        Args:
            api_key: Your LicenseChain API key
            base_url: Base URL for the API (optional)
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self._client = LicenseChainClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            retry_attempts=retry_attempts,
            retry_delay=retry_delay,
        )

    async def validate_license(
        self, license_key: str, app_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a license key.
        
        Args:
            license_key: The license key to validate
            app_id: Optional application ID for validation
            
        Returns:
            Validation result
        """
        try:
            response = await self._client.validate_license(license_key, app_id)
            return ValidationResult(
                valid=response.get("valid", False),
                license=response.get("license"),
                user=response.get("user"),
                app=response.get("app"),
                expires_at=response.get("expires_at"),
                metadata=response.get("metadata", {}),
                error=response.get("error"),
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                error=str(e),
            )

    async def is_valid(
        self, license_key: str, app_id: Optional[str] = None
    ) -> bool:
        """
        Check if license is valid (quick check).
        
        Args:
            license_key: The license key to check
            app_id: Optional application ID for validation
            
        Returns:
            True if valid, False otherwise
        """
        try:
            result = await self.validate_license(license_key, app_id)
            return result.valid
        except Exception:
            return False

    async def get_license_info(
        self, license_key: str, app_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get license information.
        
        Args:
            license_key: The license key
            app_id: Optional application ID
            
        Returns:
            License information or None if invalid
        """
        try:
            result = await self.validate_license(license_key, app_id)
            if result.valid and result.license:
                return result.license
            return None
        except Exception:
            return None

    async def is_expired(
        self, license_key: str, app_id: Optional[str] = None
    ) -> bool:
        """
        Check if license is expired.
        
        Args:
            license_key: The license key
            app_id: Optional application ID
            
        Returns:
            True if expired, False otherwise
        """
        try:
            result = await self.validate_license(license_key, app_id)
            if not result.valid or not result.license:
                return True
            
            expires_at = result.license.get("expires_at")
            if not expires_at:
                return False
            
            from datetime import datetime
            return datetime.fromisoformat(expires_at.replace("Z", "+00:00")) < datetime.now()
        except Exception:
            return True

    async def get_days_until_expiration(
        self, license_key: str, app_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Get days until expiration.
        
        Args:
            license_key: The license key
            app_id: Optional application ID
            
        Returns:
            Days until expiration or None if no expiration date
        """
        try:
            result = await self.validate_license(license_key, app_id)
            if not result.valid or not result.license:
                return None
            
            expires_at = result.license.get("expires_at")
            if not expires_at:
                return None
            
            from datetime import datetime
            exp_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            delta = exp_date - datetime.now()
            return max(0, delta.days)
        except Exception:
            return None

    async def validate_licenses(
        self, license_keys: List[str], app_id: Optional[str] = None
    ) -> List[ValidationResult]:
        """
        Validate multiple licenses.
        
        Args:
            license_keys: List of license keys to validate
            app_id: Optional application ID for validation
            
        Returns:
            List of validation results
        """
        tasks = [
            self.validate_license(key, app_id) for key in license_keys
        ]
        return await asyncio.gather(*tasks)

    async def validate_with_rules(
        self,
        license_key: str,
        app_id: Optional[str] = None,
        rules: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate with custom validation rules.
        
        Args:
            license_key: The license key to validate
            app_id: Optional application ID for validation
            rules: Custom validation rules
            
        Returns:
            Validation result with custom rules applied
        """
        result = await self.validate_license(license_key, app_id)
        
        if not result.valid or not rules:
            return result
        
        # Apply custom validation rules
        if "max_usage" in rules and result.usage_count > rules["max_usage"]:
            result.valid = False
            result.error = "Usage limit exceeded"
        
        if "allowed_features" in rules and result.features:
            allowed_features = rules["allowed_features"]
            invalid_features = [
                feature for feature in result.features
                if feature not in allowed_features
            ]
            if invalid_features:
                result.valid = False
                result.error = f"Invalid features: {', '.join(invalid_features)}"
        
        return result

    async def close(self):
        """Close the underlying client."""
        await self._client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

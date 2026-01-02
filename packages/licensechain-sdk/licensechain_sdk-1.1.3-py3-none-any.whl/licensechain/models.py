"""
LicenseChain Python SDK Models

Data models for the LicenseChain Python SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class BaseLicenseChainModel(BaseModel):
    """Base model for all LicenseChain entities."""
    
    class Config:
        extra = "allow"
        use_enum_values = True


class User(BaseLicenseChainModel):
    """User model."""
    
    id: Optional[str] = None
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    email_verified: bool = False
    status: str = "active"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == "active"


class Application(BaseLicenseChainModel):
    """Application model."""
    
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    allowed_origins: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = "active"
    license_count: int = 0
    
    @property
    def is_active(self) -> bool:
        """Check if application is active."""
        return self.status == "active"


class License(BaseLicenseChainModel):
    """License model."""
    
    id: Optional[str] = None
    key: Optional[str] = None
    app_id: str
    user_id: Optional[str] = None
    user_email: str
    user_name: Optional[str] = None
    status: str = "active"
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    features: List[str] = Field(default_factory=list)
    usage_count: int = 0
    
    @property
    def is_active(self) -> bool:
        """Check if license is active."""
        return self.status == "active"
    
    @property
    def is_expired(self) -> bool:
        """Check if license is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.now()
    
    @property
    def is_revoked(self) -> bool:
        """Check if license is revoked."""
        return self.status == "revoked"
    
    @property
    def days_until_expiration(self) -> Optional[int]:
        """Get days until expiration."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now()
        return max(0, delta.days)


class Webhook(BaseLicenseChainModel):
    """Webhook model."""
    
    id: Optional[str] = None
    app_id: str
    url: str
    events: List[str] = Field(default_factory=list)
    secret: Optional[str] = None
    status: str = "active"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    
    @property
    def is_active(self) -> bool:
        """Check if webhook is active."""
        return self.status == "active"


class Analytics(BaseLicenseChainModel):
    """Analytics model."""
    
    total_licenses: int = 0
    active_licenses: int = 0
    expired_licenses: int = 0
    revoked_licenses: int = 0
    validations_today: int = 0
    validations_this_week: int = 0
    validations_this_month: int = 0
    top_features: List[str] = Field(default_factory=list)
    usage_by_day: List[Dict[str, Any]] = Field(default_factory=list)
    usage_by_week: List[Dict[str, Any]] = Field(default_factory=list)
    usage_by_month: List[Dict[str, Any]] = Field(default_factory=list)


class PaginatedResponse(BaseLicenseChainModel):
    """Paginated response model."""
    
    data: List[Dict[str, Any]] = Field(default_factory=list)
    page: int = 1
    limit: int = 20
    total: int = 0
    total_pages: int = 1
    
    @property
    def has_next_page(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages
    
    @property
    def has_previous_page(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1
    
    @property
    def next_page(self) -> Optional[int]:
        """Get next page number."""
        return self.page + 1 if self.has_next_page else None
    
    @property
    def previous_page(self) -> Optional[int]:
        """Get previous page number."""
        return self.page - 1 if self.has_previous_page else None


class ValidationResult(BaseLicenseChainModel):
    """License validation result model."""
    
    valid: bool
    license: Optional[Dict[str, Any]] = None
    user: Optional[Dict[str, Any]] = None
    app: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def user_email(self) -> Optional[str]:
        """Get user email from validation result."""
        if self.user and "email" in self.user:
            return self.user["email"]
        return None
    
    @property
    def user_name(self) -> Optional[str]:
        """Get user name from validation result."""
        if self.user and "name" in self.user:
            return self.user["name"]
        return None
    
    @property
    def app_name(self) -> Optional[str]:
        """Get app name from validation result."""
        if self.app and "name" in self.app:
            return self.app["name"]
        return None
    
    @property
    def license_key(self) -> Optional[str]:
        """Get license key from validation result."""
        if self.license and "key" in self.license:
            return self.license["key"]
        return None
    
    @property
    def license_id(self) -> Optional[str]:
        """Get license ID from validation result."""
        if self.license and "id" in self.license:
            return self.license["id"]
        return None
    
    @property
    def features(self) -> List[str]:
        """Get features from validation result."""
        if self.license and "features" in self.license:
            return self.license["features"]
        return []
    
    @property
    def usage_count(self) -> int:
        """Get usage count from validation result."""
        if self.license and "usage_count" in self.license:
            return self.license["usage_count"]
        return 0

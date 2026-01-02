"""
LicenseChain API Client

Main client for interacting with the LicenseChain API.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field

from .exceptions import (
    AuthenticationError,
    LicenseChainException,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class LicenseChainConfig(BaseModel):
    """Configuration for LicenseChain client."""
    
    api_key: str = Field(..., description="Your LicenseChain API key")
    base_url: str = Field(default="https://api.licensechain.app", description="Base URL for the API")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")


class LicenseChainClient:
    """
    Main client for interacting with the LicenseChain API.
    
    This client provides methods for all LicenseChain API endpoints including
    authentication, license management, application management, webhooks, and analytics.
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
        Initialize the LicenseChain client.
        
        Args:
            api_key: Your LicenseChain API key
            base_url: Base URL for the API (optional, defaults to production)
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        if not api_key:
            raise ValueError("API key is required")

        self.config = LicenseChainConfig(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            retry_attempts=retry_attempts,
            retry_delay=retry_delay,
        )

        # Ensure base_url ends with /v1
        base_url = self.config.base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"
        
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(self.config.timeout),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "User-Agent": "LicenseChain-Python-SDK/1.0.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    # Authentication Methods

    async def register_user(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
        company: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            email: User's email address
            password: User's password
            name: User's full name (optional)
            company: User's company (optional)
            
        Returns:
            User registration response
        """
        payload = {
            "email": email,
            "password": password,
            "name": name,
            "company": company,
        }
        return await self._post("/auth/register", payload)

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login with email and password.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Login response with tokens
        """
        payload = {"email": email, "password": password}
        return await self._post("/auth/login", payload)

    async def logout(self) -> Dict[str, Any]:
        """
        Logout the current user.
        
        Returns:
            Logout response
        """
        return await self._post("/auth/logout")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh authentication token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response
        """
        payload = {"refresh_token": refresh_token}
        return await self._post("/auth/refresh", payload)

    async def get_user_profile(self) -> Dict[str, Any]:
        """
        Get current user profile.
        
        Returns:
            User profile data
        """
        return await self._get("/auth/me")

    async def update_user_profile(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            attributes: Profile attributes to update
            
        Returns:
            Updated user profile
        """
        return await self._patch("/auth/me", attributes)

    async def change_password(
        self, current_password: str, new_password: str
    ) -> Dict[str, Any]:
        """
        Change user password.
        
        Args:
            current_password: Current password
            new_password: New password
            
        Returns:
            Password change response
        """
        payload = {
            "current_password": current_password,
            "new_password": new_password,
        }
        return await self._patch("/auth/password", payload)

    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """
        Request password reset.
        
        Args:
            email: User's email address
            
        Returns:
            Password reset request response
        """
        payload = {"email": email}
        return await self._post("/auth/forgot-password", payload)

    async def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """
        Reset password with token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Password reset response
        """
        payload = {"token": token, "new_password": new_password}
        return await self._post("/auth/reset-password", payload)

    # Application Management

    async def create_application(
        self,
        name: str,
        description: Optional[str] = None,
        webhook_url: Optional[str] = None,
        allowed_origins: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new application.
        
        Args:
            name: Application name
            description: Application description (optional)
            webhook_url: Webhook URL (optional)
            allowed_origins: List of allowed origins (optional)
            
        Returns:
            Created application data
        """
        payload = {
            "name": name,
            "description": description,
            "webhook_url": webhook_url,
            "allowed_origins": allowed_origins or [],
        }
        return await self._post("/apps", payload)

    async def list_applications(
        self, page: int = 1, limit: int = 20
    ) -> Dict[str, Any]:
        """
        List applications with pagination.
        
        Args:
            page: Page number
            limit: Items per page
            
        Returns:
            Paginated list of applications
        """
        params = {"page": page, "limit": limit}
        return await self._get("/apps", params)

    async def get_application(self, app_id: str) -> Dict[str, Any]:
        """
        Get application details.
        
        Args:
            app_id: Application ID
            
        Returns:
            Application data
        """
        return await self._get(f"/apps/{app_id}")

    async def update_application(
        self, app_id: str, attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update application.
        
        Args:
            app_id: Application ID
            attributes: Attributes to update
            
        Returns:
            Updated application data
        """
        return await self._patch(f"/apps/{app_id}", attributes)

    async def delete_application(self, app_id: str) -> Dict[str, Any]:
        """
        Delete application.
        
        Args:
            app_id: Application ID
            
        Returns:
            Deletion response
        """
        return await self._delete(f"/apps/{app_id}")

    async def regenerate_api_key(self, app_id: str) -> Dict[str, Any]:
        """
        Regenerate API key for application.
        
        Args:
            app_id: Application ID
            
        Returns:
            New API key data
        """
        return await self._post(f"/apps/{app_id}/regenerate-key")

    # License Management

    async def create_license(
        self,
        app_id: str,
        user_email: str,
        user_name: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new license.
        
        Args:
            app_id: Application ID
            user_email: User's email address
            user_name: User's name (optional)
            expires_at: Expiration date (optional)
            metadata: License metadata (optional)
            
        Returns:
            Created license data
        """
        payload = {
            "app_id": app_id,
            "user_email": user_email,
            "user_name": user_name,
            "expires_at": expires_at,
            "metadata": metadata or {},
        }
        return await self._post("/licenses", payload)

    async def list_licenses(
        self,
        app_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List licenses with filters.
        
        Args:
            app_id: Application ID filter (optional)
            page: Page number
            limit: Items per page
            status: License status filter (optional)
            
        Returns:
            Paginated list of licenses
        """
        params = {"page": page, "limit": limit}
        if app_id:
            params["app_id"] = app_id
        if status:
            params["status"] = status
        return await self._get("/licenses", params)

    async def get_license(self, license_id: str) -> Dict[str, Any]:
        """
        Get license details.
        
        Args:
            license_id: License ID
            
        Returns:
            License data
        """
        return await self._get(f"/licenses/{license_id}")

    async def update_license(
        self, license_id: str, attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update license.
        
        Args:
            license_id: License ID
            attributes: Attributes to update
            
        Returns:
            Updated license data
        """
        return await self._patch(f"/licenses/{license_id}", attributes)

    async def delete_license(self, license_id: str) -> Dict[str, Any]:
        """
        Delete license.
        
        Args:
            license_id: License ID
            
        Returns:
            Deletion response
        """
        return await self._delete(f"/licenses/{license_id}")

    async def validate_license(
        self, license_key: str, app_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a license key.
        
        Args:
            license_key: License key to validate
            app_id: Application ID for validation (optional)
            
        Returns:
            License validation result
        """
        # Use /licenses/verify endpoint with 'key' parameter to match API
        payload = {"key": license_key}
        if app_id:
            payload["app_id"] = app_id
        return await self._post("/licenses/verify", payload)

    async def revoke_license(
        self, license_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Revoke a license.
        
        Args:
            license_id: License ID
            reason: Revocation reason (optional)
            
        Returns:
            Revocation response
        """
        payload = {"reason": reason}
        return await self._patch(f"/licenses/{license_id}/revoke", payload)

    async def activate_license(self, license_id: str) -> Dict[str, Any]:
        """
        Activate a license.
        
        Args:
            license_id: License ID
            
        Returns:
            Activation response
        """
        return await self._patch(f"/licenses/{license_id}/activate")

    async def extend_license(
        self, license_id: str, new_expires_at: str
    ) -> Dict[str, Any]:
        """
        Extend license expiration.
        
        Args:
            license_id: License ID
            new_expires_at: New expiration date
            
        Returns:
            Extension response
        """
        payload = {"expires_at": new_expires_at}
        return await self._patch(f"/licenses/{license_id}/extend", payload)

    # Webhook Management

    async def create_webhook(
        self,
        app_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a webhook.
        
        Args:
            app_id: Application ID
            url: Webhook URL
            events: List of events to subscribe to
            secret: Webhook secret (optional)
            
        Returns:
            Created webhook data
        """
        payload = {
            "app_id": app_id,
            "url": url,
            "events": events,
            "secret": secret,
        }
        return await self._post("/webhooks", payload)

    async def list_webhooks(self, app_id: Optional[str] = None) -> Dict[str, Any]:
        """
        List webhooks.
        
        Args:
            app_id: Application ID filter (optional)
            
        Returns:
            List of webhooks
        """
        params = {}
        if app_id:
            params["app_id"] = app_id
        return await self._get("/webhooks", params)

    async def get_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """
        Get webhook details.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Webhook data
        """
        return await self._get(f"/webhooks/{webhook_id}")

    async def update_webhook(
        self, webhook_id: str, attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update webhook.
        
        Args:
            webhook_id: Webhook ID
            attributes: Attributes to update
            
        Returns:
            Updated webhook data
        """
        return await self._patch(f"/webhooks/{webhook_id}", attributes)

    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """
        Delete webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Deletion response
        """
        return await self._delete(f"/webhooks/{webhook_id}")

    async def test_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """
        Test webhook.
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Test response
        """
        return await self._post(f"/webhooks/{webhook_id}/test")

    # Analytics

    async def get_analytics(
        self,
        app_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metric: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get analytics data.
        
        Args:
            app_id: Application ID filter (optional)
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            metric: Metric filter (optional)
            
        Returns:
            Analytics data
        """
        params = {}
        if app_id:
            params["app_id"] = app_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if metric:
            params["metric"] = metric
        return await self._get("/analytics", params)

    async def get_license_analytics(self, license_id: str) -> Dict[str, Any]:
        """
        Get license analytics.
        
        Args:
            license_id: License ID
            
        Returns:
            License analytics data
        """
        return await self._get(f"/licenses/{license_id}/analytics")

    async def get_usage_stats(
        self, app_id: Optional[str] = None, period: str = "30d"
    ) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Args:
            app_id: Application ID filter (optional)
            period: Time period (default: 30d)
            
        Returns:
            Usage statistics
        """
        params = {"period": period}
        if app_id:
            params["app_id"] = app_id
        return await self._get("/analytics/usage", params)

    async def get_dashboard_insights(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard insights (basic and advanced analytics).
        
        Returns:
            Dashboard insights including:
            - Revenue metrics (current vs previous period)
            - License statistics
            - App statistics
            - Growth metrics
            - Advanced analytics (if tier allows)
        """
        return await self._get("/dashboard/insights")

    async def get_advanced_analytics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        metric: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get advanced analytics data (requires Pro+ tier).
        
        Args:
            start_date: Start date filter (ISO format, optional)
            end_date: End date filter (ISO format, optional)
            metric: Specific metric to retrieve (optional)
            
        Returns:
            Advanced analytics data
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if metric:
            params["metric"] = metric
        return await self._get("/dashboard/insights", params)

    # Product Management (Seller/Admin only)

    async def list_products(
        self,
        limit: int = 50,
        offset: int = 0,
        active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List products (Seller/Admin only).
        
        Args:
            limit: Number of products to return
            offset: Offset for pagination
            active: Filter by active status (optional)
            search: Search term for product name (optional)
            
        Returns:
            List of products with statistics
        """
        params = {"limit": limit, "offset": offset}
        if active is not None:
            params["active"] = str(active).lower()
        if search:
            params["search"] = search
        return await self._get("/seller/products", params)

    async def create_product(
        self,
        name: str,
        price: float,
        description: Optional[str] = None,
        currency: str = "USD",
        active: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new product (Seller/Admin only).
        
        Args:
            name: Product name
            price: Product price
            description: Product description (optional)
            currency: Currency code (default: USD)
            active: Whether product is active (default: True)
            
        Returns:
            Created product data
        """
        payload = {
            "name": name,
            "price": price,
            "description": description,
            "currency": currency,
            "active": active,
        }
        return await self._post("/seller/products", payload)

    async def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
        currency: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update a product (Seller/Admin only).
        
        Args:
            product_id: Product ID
            name: Product name (optional)
            price: Product price (optional)
            description: Product description (optional)
            currency: Currency code (optional)
            active: Whether product is active (optional)
            
        Returns:
            Updated product data
        """
        payload = {"id": product_id}
        if name is not None:
            payload["name"] = name
        if price is not None:
            payload["price"] = price
        if description is not None:
            payload["description"] = description
        if currency is not None:
            payload["currency"] = currency
        if active is not None:
            payload["active"] = active
        return await self._patch("/seller/products", payload)

    async def delete_product(self, product_id: str) -> Dict[str, Any]:
        """
        Delete a product (Seller/Admin only).
        
        Args:
            product_id: Product ID
            
        Returns:
            Deletion response
        """
        params = {"id": product_id}
        return await self._delete("/seller/products", params)

    async def get_product_analytics(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get product analytics (Seller/Admin only).
        
        Args:
            product_id: Product ID filter (optional, if not provided returns all products)
            
        Returns:
            Product analytics data
        """
        params = {}
        if product_id:
            params["product_id"] = product_id
        return await self._get("/seller/analytics", params)

    # Team Management (Pro+ tier)

    async def list_teams(self) -> Dict[str, Any]:
        """
        List teams where user is owner or member (Pro+ tier).
        
        Returns:
            List of teams with members and access information
        """
        return await self._get("/teams")

    async def create_team(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new team (Pro+ tier).
        
        Args:
            name: Team name
            description: Team description (optional)
            
        Returns:
            Created team data
        """
        payload = {
            "name": name,
            "description": description,
        }
        return await self._post("/teams", payload)

    async def get_team(self, team_id: str) -> Dict[str, Any]:
        """
        Get team details (Pro+ tier).
        
        Args:
            team_id: Team ID
            
        Returns:
            Team data with members and access information
        """
        return await self._get(f"/teams/{team_id}")

    async def update_team(
        self,
        team_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update team (Pro+ tier).
        
        Args:
            team_id: Team ID
            name: Team name (optional)
            description: Team description (optional)
            
        Returns:
            Updated team data
        """
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        return await self._patch(f"/teams/{team_id}", payload)

    async def delete_team(self, team_id: str) -> Dict[str, Any]:
        """
        Delete team (Pro+ tier, owner only).
        
        Args:
            team_id: Team ID
            
        Returns:
            Deletion response
        """
        return await self._delete(f"/teams/{team_id}")

    async def invite_team_member(
        self,
        team_id: str,
        email: str,
        role: str = "member",
    ) -> Dict[str, Any]:
        """
        Invite a member to the team (Pro+ tier).
        
        Args:
            team_id: Team ID
            email: Email address of the user to invite
            role: Member role (owner, admin, member)
            
        Returns:
            Invitation response
        """
        payload = {
            "email": email,
            "role": role,
        }
        return await self._post(f"/teams/{team_id}/members", payload)

    async def list_team_members(self, team_id: str) -> Dict[str, Any]:
        """
        List team members (Pro+ tier).
        
        Args:
            team_id: Team ID
            
        Returns:
            List of team members
        """
        return await self._get(f"/teams/{team_id}/members")

    async def update_team_member(
        self,
        team_id: str,
        member_id: str,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update team member role (Pro+ tier).
        
        Args:
            team_id: Team ID
            member_id: Member ID
            role: New role (owner, admin, member)
            
        Returns:
            Updated member data
        """
        payload = {}
        if role is not None:
            payload["role"] = role
        return await self._patch(f"/teams/{team_id}/members/{member_id}", payload)

    async def remove_team_member(
        self,
        team_id: str,
        member_id: str,
    ) -> Dict[str, Any]:
        """
        Remove member from team (Pro+ tier).
        
        Args:
            team_id: Team ID
            member_id: Member ID
            
        Returns:
            Removal response
        """
        return await self._delete(f"/teams/{team_id}/members/{member_id}")

    async def accept_team_invitation(self, team_id: str) -> Dict[str, Any]:
        """
        Accept team invitation (Pro+ tier).
        
        Args:
            team_id: Team ID
            
        Returns:
            Acceptance response
        """
        return await self._post(f"/teams/{team_id}/accept")

    async def share_app_with_team(
        self,
        team_id: str,
        app_id: str,
    ) -> Dict[str, Any]:
        """
        Share app with team (Pro+ tier).
        
        Args:
            team_id: Team ID
            app_id: Application ID
            
        Returns:
            Sharing response
        """
        return await self._post(f"/teams/{team_id}/apps", {"appId": app_id})

    async def list_team_apps(self, team_id: str) -> Dict[str, Any]:
        """
        List apps shared with team (Pro+ tier).
        
        Args:
            team_id: Team ID
            
        Returns:
            List of shared apps
        """
        return await self._get(f"/teams/{team_id}/apps")

    async def remove_app_from_team(
        self,
        team_id: str,
        app_id: str,
    ) -> Dict[str, Any]:
        """
        Remove app from team access (Pro+ tier).
        
        Args:
            team_id: Team ID
            app_id: Application ID
            
        Returns:
            Removal response
        """
        return await self._delete(f"/teams/{team_id}/apps/{app_id}")

    # System Status

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status.
        
        Returns:
            System status data
        """
        return await self._get("/status")

    async def get_health_check(self) -> Dict[str, Any]:
        """
        Get health check.
        
        Returns:
            Health check data
        """
        return await self._get("/health")

    # HTTP Methods

    async def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        url = path
        if params:
            url += f"?{urlencode(params)}"
        
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._client.get(url)
                return await self._process_response(response)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

    async def _post(
        self, path: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        # Ensure path starts with /
        url = path if path.startswith("/") else f"/{path}"
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._client.post(url, json=payload)
                return await self._process_response(response)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

    async def _patch(
        self, path: str, payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._client.patch(path, json=payload)
                return await self._process_response(response)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

    async def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a DELETE request."""
        # Ensure path starts with /
        url = path if path.startswith("/") else f"/{path}"
        if params:
            url += f"?{urlencode(params)}"
        for attempt in range(self.config.retry_attempts):
            try:
                response = await self._client.delete(url)
                return await self._process_response(response)
            except Exception as e:
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

    async def _process_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process HTTP response and handle errors."""
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {"error": "Invalid JSON response"}

        if not response.is_success:
            error_message = data.get("error", f"HTTP {response.status_code}")
            
            if response.status_code == 400:
                raise ValidationError(error_message)
            elif response.status_code in (401, 403):
                raise AuthenticationError(error_message)
            elif response.status_code == 404:
                raise NotFoundError(error_message)
            elif response.status_code == 429:
                raise RateLimitError(error_message)
            elif 500 <= response.status_code < 600:
                raise ServerError(error_message)
            else:
                raise LicenseChainException(error_message)

        return data

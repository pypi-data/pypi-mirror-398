from typing import Optional

from .api_client import ApiClient
from .exceptions import ConfigurationError
from .services import LicenseService, ProductService, UserService, WebhookService


class Client:
    """Main client for LicenseChain API."""
    
    def __init__(self, api_key: str, base_url: str = 'https://api.licensechain.app', 
                 timeout: int = 30, retries: int = 3):
        if not api_key:
            raise ConfigurationError("API key is required")
        
        self.api_client = ApiClient(api_key, base_url, timeout, retries)
        
        # Initialize services
        self.licenses = LicenseService(self.api_client)
        self.users = UserService(self.api_client)
        self.products = ProductService(self.api_client)
        self.webhooks = WebhookService(self.api_client)
    
    def ping(self) -> dict:
        """Ping the API."""
        return self.api_client.ping()
    
    def health(self) -> dict:
        """Check API health."""
        return self.api_client.health()
    
    def close(self):
        """Close the client."""
        self.api_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

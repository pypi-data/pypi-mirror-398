from typing import Any, Dict, List, Optional

from ..exceptions import ValidationError
from ..utils import validate_uuid, validate_not_empty, validate_positive, validate_currency, sanitize_metadata, validate_pagination
from ..models import Product, ProductStats


class ProductService:
    """Service for product management."""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def create(self, name: str, description: Optional[str] = None, 
               price: Optional[float] = None, currency: str = 'USD', 
               metadata: Optional[Dict[str, Any]] = None) -> Product:
        """Create a new product."""
        self._validate_required_params(name, price, currency)
        
        data = {
            'name': name,
            'description': description,
            'price': price,
            'currency': currency,
            'metadata': sanitize_metadata(metadata or {})
        }
        
        response = self.api_client.post('/products', data)
        return Product(**response['data'])
    
    def get(self, product_id: str) -> Product:
        """Get a product by ID."""
        self._validate_uuid(product_id, 'product_id')
        
        response = self.api_client.get(f'/products/{product_id}')
        return Product(**response['data'])
    
    def update(self, product_id: str, updates: Dict[str, Any]) -> Product:
        """Update a product."""
        self._validate_uuid(product_id, 'product_id')
        
        response = self.api_client.put(f'/products/{product_id}', sanitize_metadata(updates))
        return Product(**response['data'])
    
    def delete(self, product_id: str) -> bool:
        """Delete a product."""
        self._validate_uuid(product_id, 'product_id')
        
        self.api_client.delete(f'/products/{product_id}')
        return True
    
    def list(self, page: Optional[int] = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """List products."""
        page, limit = validate_pagination(page, limit)
        
        response = self.api_client.get('/products', {
            'page': page,
            'limit': limit
        })
        
        return {
            'data': [Product(**product) for product in response['data']],
            'total': response['total'],
            'page': response['page'],
            'limit': response['limit']
        }
    
    def stats(self) -> ProductStats:
        """Get product statistics."""
        response = self.api_client.get('/products/stats')
        return ProductStats(**response['data'])
    
    def _validate_required_params(self, name: str, price: float, currency: str) -> None:
        """Validate required parameters."""
        validate_not_empty(name, 'name')
        validate_positive(price, 'price')
        if not validate_currency(currency):
            raise ValidationError('Invalid currency')
    
    def _validate_uuid(self, id_value: str, field_name: str) -> None:
        """Validate UUID format."""
        validate_not_empty(id_value, field_name)
        if not validate_uuid(id_value):
            raise ValidationError(f"Invalid {field_name} format")

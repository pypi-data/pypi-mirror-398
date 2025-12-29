"""
Actory API Client

Main client class for interacting with the Actory ACP API.
"""

import requests
from typing import Optional, List, Dict, Any
from .models import Product, Merchant, SearchResult


class ActoryError(Exception):
    """Base exception for Actory SDK errors"""
    pass


class AuthenticationError(ActoryError):
    """Raised when API key is invalid or missing"""
    pass


class RateLimitError(ActoryError):
    """Raised when rate limit is exceeded"""
    pass


class Actory:
    """
    Actory API Client
    
    Official Python client for the Actory Agent Commerce Protocol (ACP) API.
    
    Args:
        api_key: Your Actory API key (starts with 'act_sk_')
        base_url: API base URL (default: https://actory.ai/api)
    
    Example:
        >>> from actory import Actory
        >>> client = Actory(api_key="act_sk_...")
        >>> results = client.search("red shoes", max_price=50)
        >>> for product in results.products:
        ...     print(f"{product.title}: ${product.price}")
    """
    
    DEFAULT_BASE_URL = "https://app.actory.ai/api"
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith("act_"):
            raise ValueError("Invalid API key format. Keys should start with 'act_'")
        
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "actory-python/0.1.0",
        })
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make an API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self._session.request(method, url, params=params)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded. Please slow down your requests.")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ActoryError(f"Request failed: {e}")
    
    def search(
        self,
        query: str,
        *,
        in_stock: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        vendor: Optional[str] = None,
        category: Optional[str] = None,
        merchant_id: Optional[str] = None,
        limit: int = 20,
        page: int = 1,
    ) -> SearchResult:
        """
        Search the product catalog.
        
        Args:
            query: Search query string
            in_stock: Filter to in-stock products only
            min_price: Minimum price filter
            max_price: Maximum price filter
            vendor: Filter by vendor/brand
            category: Filter by category tag
            merchant_id: Filter by specific merchant
            limit: Results per page (max 100)
            page: Page number
        
        Returns:
            SearchResult with products and pagination info
        
        Example:
            >>> results = client.search("shoes", max_price=100, in_stock=True)
            >>> print(f"Found {results.total} products")
        """
        params = {"q": query, "limit": limit, "page": page}
        
        if in_stock is not None:
            params["inStock"] = str(in_stock).lower()
        if min_price is not None:
            params["minPrice"] = min_price
        if max_price is not None:
            params["maxPrice"] = max_price
        if vendor:
            params["vendor"] = vendor
        if category:
            params["category"] = category
        if merchant_id:
            params["merchantId"] = merchant_id
        
        data = self._request("GET", "/v1/catalog/search", params=params)
        return SearchResult.from_dict(data)
    
    def nl_search(self, query: str, limit: int = 20, page: int = 1) -> SearchResult:
        """
        Natural language search.
        
        Parse natural language queries like "red shoes under $50 in stock".
        
        Args:
            query: Natural language search query
            limit: Results per page (max 100)
            page: Page number
        
        Returns:
            SearchResult with products and parsed query info
        
        Example:
            >>> results = client.nl_search("red shoes under $50")
        """
        params = {"q": query, "limit": limit, "page": page}
        data = self._request("GET", "/v1/catalog/nl-search", params=params)
        return SearchResult.from_dict(data)
    
    def get_product(self, product_id: str) -> Product:
        """
        Get a product by ID.
        
        Args:
            product_id: The product ID
        
        Returns:
            Product details
        """
        data = self._request("GET", f"/v1/catalog/products/{product_id}")
        return Product.from_dict(data.get("product", data))
    
    def list_merchants(self, limit: int = 20, page: int = 1) -> List[Merchant]:
        """
        List all merchants.
        
        Args:
            limit: Results per page
            page: Page number
        
        Returns:
            List of merchants
        """
        params = {"limit": limit, "page": page}
        data = self._request("GET", "/v1/merchants", params=params)
        return [Merchant.from_dict(m) for m in data.get("merchants", [])]
    
    def get_merchant(self, merchant_id: str) -> Merchant:
        """
        Get a merchant by ID.
        
        Args:
            merchant_id: The merchant ID
        
        Returns:
            Merchant details
        """
        data = self._request("GET", f"/v1/merchants/{merchant_id}")
        return Merchant.from_dict(data.get("merchant", data))
    
    def list_categories(self) -> List[str]:
        """Get all available product categories."""
        data = self._request("GET", "/v1/catalog/categories")
        return data.get("categories", [])
    
    def list_vendors(self) -> List[str]:
        """Get all available vendors/brands."""
        data = self._request("GET", "/v1/catalog/vendors")
        return data.get("vendors", [])
    
    # Convenience aliases
    def get_merchants(self, limit: int = 20, page: int = 1) -> List[Merchant]:
        """Alias for list_merchants() for convenience."""
        return self.list_merchants(limit=limit, page=page)
    
    def get_products(self, limit: int = 20, page: int = 1) -> SearchResult:
        """Get all products (convenience method that calls search with empty query)."""
        return self.search("", limit=limit, page=page)

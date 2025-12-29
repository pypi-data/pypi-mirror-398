"""
Actory ACP data models
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class Product:
    """ACP-compliant product representation"""
    id: str
    title: str
    price: float
    currency: str
    in_stock: bool
    merchant_id: str
    description: Optional[str] = None
    images: Optional[List[str]] = None
    vendor: Optional[str] = None
    quantity: Optional[int] = None
    sku: Optional[str] = None
    tags: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Product":
        """Create Product from API response dict
        
        Handles missing/null fields gracefully since API responses may vary.
        """
        # Handle price - may be null, missing, or in nested structure
        price = data.get("price")
        if price is None:
            # Try to get from priceRange if available
            price_range = data.get("priceRange", {})
            min_price = price_range.get("minVariantPrice", {})
            price = min_price.get("amount", 0.0)
        
        # Convert price to float safely
        try:
            price = float(price) if price else 0.0
        except (ValueError, TypeError):
            price = 0.0
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", "Untitled"),
            price=price,
            currency=data.get("currency", "USD"),
            in_stock=data.get("inStock", data.get("in_stock", True)),
            merchant_id=data.get("merchantId", data.get("merchant_id", "")),
            description=data.get("description"),
            images=data.get("images", []),
            vendor=data.get("vendor"),
            quantity=data.get("quantity"),
            sku=data.get("sku"),
            tags=data.get("tags", []),
        )


@dataclass
class Merchant:
    """Merchant representation"""
    id: str
    name: str
    domain: str
    product_count: int

    @classmethod
    def from_dict(cls, data: dict) -> "Merchant":
        """Create Merchant from API response dict"""
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            domain=data.get("domain", ""),
            product_count=data.get("productCount", 0),
        )


@dataclass
class SearchResult:
    """Search result with products and pagination"""
    products: List[Product]
    total: int
    page: int
    total_pages: int

    @classmethod
    def from_dict(cls, data: dict) -> "SearchResult":
        """Create SearchResult from API response dict"""
        products = [Product.from_dict(p) for p in data.get("products", [])]
        pagination = data.get("pagination", {})
        return cls(
            products=products,
            total=pagination.get("total", len(products)),
            page=pagination.get("page", 1),
            total_pages=pagination.get("totalPages", 1),
        )

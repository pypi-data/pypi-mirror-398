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
        
        The API returns products with nested structure:
        - Price is in variants[0].price.amount
        - Currency is in variants[0].price.currency
        - Stock status is in variants[0].availability.status
        - Merchant ID is in merchant.id
        """
        # Extract first variant (primary variant)
        variants = data.get("variants", [])
        first_variant = variants[0] if variants else {}
        
        # Parse price from nested structure
        price_obj = first_variant.get("price", {})
        try:
            price = float(price_obj.get("amount", 0)) if price_obj else 0.0
        except (ValueError, TypeError):
            price = 0.0
        
        # Parse currency
        currency = price_obj.get("currency", "USD") if price_obj else "USD"
        
        # Parse availability from nested structure
        availability = first_variant.get("availability", {})
        stock_status = availability.get("status", "in_stock")
        in_stock = stock_status == "in_stock"
        quantity = availability.get("quantity")
        
        # Parse merchant from nested structure
        merchant = data.get("merchant", {})
        merchant_id = merchant.get("id", "")
        
        # Parse SKU from first variant
        sku = first_variant.get("sku")
        
        return cls(
            id=data.get("id", ""),
            title=data.get("title", "Untitled"),
            price=price,
            currency=currency,
            in_stock=in_stock,
            merchant_id=merchant_id,
            description=data.get("description"),
            images=data.get("images", []),
            vendor=data.get("vendor"),  # May be None as API doesn't return this
            quantity=quantity,
            sku=sku,
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

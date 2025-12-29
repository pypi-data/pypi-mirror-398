"""
Actory Python SDK

Official Python client for the Actory Agent Commerce Protocol (ACP) API.
Enables AI agents to search and interact with e-commerce product catalogs.

Usage:
    from actory import Actory
    client = Actory(api_key="act_sk_...")
    results = client.search("red shoes", max_price=50)
"""

from .client import Actory, ActoryError, AuthenticationError, RateLimitError
from .models import Product, Merchant, SearchResult

__version__ = "0.1.4"
__all__ = [
    "Actory",
    "ActoryError",
    "AuthenticationError", 
    "RateLimitError",
    "Product",
    "Merchant",
    "SearchResult",
]

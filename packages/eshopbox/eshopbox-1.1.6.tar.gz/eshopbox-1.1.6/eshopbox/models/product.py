"""Product model"""

from typing import Optional, List
from pydantic import BaseModel, Field


class Product(BaseModel):
    """Represents a product item"""

    sku: str = Field(..., description="Unique product SKU")
    name: str = Field(..., description="Product name")
    weight: Optional[float] = Field(None, description="Weight in kg")
    height: Optional[float] = Field(None)
    width: Optional[float] = Field(None)
    length: Optional[float] = Field(None)
    price: Optional[float] = Field(None, description="Selling price")
    quantity: Optional[int] = Field(None, description="Available quantity")

    tags: Optional[List[str]] = Field(default=None, description="Product tags list")

"""Order model"""

from typing import Optional, List
from pydantic import BaseModel, Field

from eshopbox.models.address import Address
from eshopbox.models.product import Product


class OrderItem(BaseModel):
    """Represents an item inside an order."""

    sku: str = Field(..., description="Product SKU")
    name: Optional[str] = Field(None)
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    price: float = Field(..., ge=0, description="Unit price")


class PaymentInfo(BaseModel):
    """Order payment details"""

    method: str = Field(..., description="Payment method e.g. COD, Prepaid")
    transaction_id: Optional[str] = Field(None, description="Payment transaction ID")
    amount: float = Field(..., ge=0, description="Paid amount")


class Order(BaseModel):
    """Represents an order."""

    customer_order_number: str = Field(..., description="Unique external customer order number")
    channel_id: str = Field(..., description="Channel identifier")

    shipping_address: Address
    billing_address: Optional[Address] = None

    items: List[OrderItem] = Field(..., description="Order item list")
    payment: Optional[PaymentInfo] = Field(None, description="Payment details")

    order_date: Optional[str] = Field(None, description="Order timestamp")
    status: Optional[str] = Field(None, description="Order status")

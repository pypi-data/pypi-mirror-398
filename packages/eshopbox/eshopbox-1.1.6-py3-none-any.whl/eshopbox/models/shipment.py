"""Shipment model"""

from typing import Optional, List
from pydantic import BaseModel, Field
from eshopbox.models.address import Address


class ShipmentItem(BaseModel):
    """Represents an item inside a shipment."""

    sku: str = Field(..., description="Product SKU")
    quantity: int = Field(..., ge=1, description="Quantity shipped")


class Shipment(BaseModel):
    """Represents a shipment."""

    shipment_id: str = Field(..., description="Unique shipment ID")
    awb_number: Optional[str] = Field(None, description="Airway bill number")
    courier: Optional[str] = Field(None, description="Courier partner name")

    sender: Address
    recipient: Address

    items: List[ShipmentItem] = Field(..., description="List of items in shipment")
    status: Optional[str] = Field(None, description="Shipment current status")

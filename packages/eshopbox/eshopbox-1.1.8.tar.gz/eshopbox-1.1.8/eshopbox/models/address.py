"""Address model"""

from typing import Optional
from pydantic import BaseModel, Field, validator


class Address(BaseModel):
    """Represents a customer or warehouse address."""

    name: str = Field(..., description="Full name of the recipient")
    line1: str = Field(..., description="Address line 1")
    line2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State name")
    pincode: str = Field(..., min_length=6, max_length=6, description="6-digit postal code")
    phone: str = Field(..., min_length=10, max_length=15, description="Contact number")
    email: Optional[str] = Field(None, description="Email address")

    @validator("pincode")
    def validate_pincode(cls, v):
        if not v.isdigit():
            raise ValueError("Pincode must contain only digits")
        return v

"""
Order Pydantic schemas — Create, Response, StatusUpdate.
Updated with payment_status, price breakdown fields, and subtotal per item.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.schemas.address import AddressResponse


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v


class OrderCreate(BaseModel):
    address_id: int
    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v: List[OrderItemCreate]) -> List[OrderItemCreate]:
        if not v:
            raise ValueError("Order must have at least one item")
        return v


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    image_url: Optional[str] = None
    quantity: int
    price: Decimal          # price snapshot at time of purchase
    subtotal: Decimal       # price × quantity


class OrderResponse(BaseModel):
    id: int
    status: str
    payment_status: str
    subtotal: Decimal
    tax: Decimal
    shipping_fee: Decimal
    total_amount: Decimal
    shipping_address: Optional[AddressResponse] = None
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        valid = {
            "PENDING", "PAYMENT_PENDING", "PAYMENT_FAILED",
            "CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED",
            "CANCELLED", "REFUNDED",
        }
        if v.upper() not in valid:
            raise ValueError(f"Status must be one of: {valid}")
        return v.upper()


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = None

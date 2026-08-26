"""
Cart Pydantic schemas — request/response DTOs.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, field_validator


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v


class CartItemUpdate(BaseModel):
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Quantity must be at least 1")
        return v


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    product_brand: Optional[str] = None
    unit_price: Decimal       # effective price (discount_price if available)
    original_price: Decimal   # always product.price
    quantity: int
    subtotal: Decimal
    in_stock: bool
    available_stock: int
    added_at: datetime

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse] = []
    item_count: int
    subtotal: Decimal
    total_discount: Decimal
    total: Decimal

    model_config = {"from_attributes": True}


class CartSummary(BaseModel):
    """Lightweight cart summary for navbar badge."""
    item_count: int
    total: Decimal

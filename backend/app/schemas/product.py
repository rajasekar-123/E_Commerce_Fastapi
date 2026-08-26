"""
Product Pydantic schemas — Create, Update, Response, SearchParams.
Updated to include brand field.
"""

from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, field_validator


class SortOption(str, Enum):
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    RATING_DESC = "rating_desc"
    NEWEST = "newest"


class ProductCreate(BaseModel):
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    stock: int = 0
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_active: bool = True

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("discount_price")
    @classmethod
    def discount_less_than_price(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        return v  # Cross-field validation done in service

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[Decimal] = None
    discount_price: Optional[Decimal] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    brand: Optional[str] = None
    price: Decimal
    discount_price: Optional[Decimal] = None
    stock: int
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    rating: Optional[float] = None
    review_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_category(cls, product) -> "ProductResponse":
        return cls(
            id=product.id,
            sku=product.sku,
            name=product.name,
            description=product.description,
            brand=getattr(product, "brand", None),
            price=product.price,
            discount_price=product.discount_price,
            stock=product.stock,
            image_url=product.image_url,
            category_id=product.category_id,
            rating=product.rating,
            review_count=product.review_count,
            is_active=product.is_active,
            created_at=product.created_at,
        )


class ProductSearchParams(BaseModel):
    query: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    sort: Optional[SortOption] = None
    skip: int = 0
    limit: int = 20

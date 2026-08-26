"""Review Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, field_validator


class ReviewCreate(BaseModel):
    rating: int
    comment: str | None = None

    @field_validator("rating")
    @classmethod
    def rating_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ReviewResponse(BaseModel):
    id: int
    product_id: int
    user_name: str
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

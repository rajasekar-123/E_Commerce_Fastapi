"""Category Pydantic schemas — Create, Update, Response."""

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    image_url: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}

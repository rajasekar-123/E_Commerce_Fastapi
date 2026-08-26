"""Address Pydantic schemas."""

from pydantic import BaseModel


class AddressCreate(BaseModel):
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool = False


class AddressResponse(BaseModel):
    id: int
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None
    is_default: bool

    model_config = {"from_attributes": True}

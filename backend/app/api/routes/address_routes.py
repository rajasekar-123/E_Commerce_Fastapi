"""Address routes."""

from typing import List
from fastapi import APIRouter, Depends

from app.api.dependencies import get_address_service
from app.core.security import get_current_user
from app.schemas.address import AddressCreate, AddressResponse

router = APIRouter()


@router.get(
    "/addresses",
    response_model=List[AddressResponse],
    summary="Get current user's shipping addresses",
)
async def get_addresses(
    current_user=Depends(get_current_user),
    address_service=Depends(get_address_service),
) -> List[AddressResponse]:
    return await address_service.get_user_addresses(current_user.id)


@router.post(
    "/addresses",
    response_model=AddressResponse,
    status_code=201,
    summary="Add a new shipping address",
)
async def add_address(
    request: AddressCreate,
    current_user=Depends(get_current_user),
    address_service=Depends(get_address_service),
) -> AddressResponse:
    return await address_service.add_address(current_user.id, request)


@router.delete(
    "/addresses/{address_id}",
    status_code=204,
    summary="Delete a shipping address",
)
async def delete_address(
    address_id: int,
    current_user=Depends(get_current_user),
    address_service=Depends(get_address_service),
) -> None:
    await address_service.delete_address(address_id, current_user.id)

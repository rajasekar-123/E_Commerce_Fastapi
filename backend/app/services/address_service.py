"""Address Service — user address management."""

from typing import List

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.address import Address
from app.repositories.address_repository import AddressRepository
from app.repositories.user_repository import UserRepository
from app.schemas.address import AddressCreate, AddressResponse


class AddressService:

    def __init__(
        self,
        address_repo: AddressRepository,
        user_repo: UserRepository,
    ):
        self._address_repo = address_repo
        self._user_repo = user_repo

    async def get_user_addresses(self, user_id: int) -> List[AddressResponse]:
        """Get all addresses for a user (default address returned first)."""
        addresses = await self._address_repo.find_by_user_id(user_id)
        return [AddressResponse.model_validate(a) for a in addresses]

    async def add_address(self, user_id: int, data: AddressCreate) -> AddressResponse:
        """Add a new shipping address for the user."""
        address = Address(
            user_id=user_id,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            is_default=data.is_default,
        )
        saved = await self._address_repo.save(address)
        return AddressResponse.model_validate(saved)

    async def delete_address(self, address_id: int, user_id: int) -> None:
        """Delete an address. Verifies ownership before deletion."""
        address = await self._address_repo.find_by_id(address_id)
        if address is None:
            raise NotFoundError(f"Address with id={address_id} not found")
        if address.user_id != user_id:
            raise ForbiddenError("You do not own this address")
        await self._address_repo.delete(address)

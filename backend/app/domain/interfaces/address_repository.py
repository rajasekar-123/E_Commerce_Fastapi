"""Abstract repository interface for Address entity."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.address import Address


class IAddressRepository(ABC):

    @abstractmethod
    async def find_by_id(self, address_id: int) -> Optional[Address]: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> List[Address]: ...

    @abstractmethod
    async def save(self, address: Address) -> Address: ...

    @abstractmethod
    async def delete(self, address: Address) -> None: ...

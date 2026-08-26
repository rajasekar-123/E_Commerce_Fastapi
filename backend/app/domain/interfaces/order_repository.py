"""Abstract repository interface for Order entity."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.order import Order


class IOrderRepository(ABC):

    @abstractmethod
    async def find_by_id(self, order_id: int) -> Optional[Order]: ...

    @abstractmethod
    async def find_by_user_id(self, user_id: int) -> List[Order]: ...

    @abstractmethod
    async def find_all(self) -> List[Order]: ...

    @abstractmethod
    async def save(self, order: Order) -> Order: ...

    @abstractmethod
    async def count(self) -> int: ...

"""Abstract repository interface for Product entity."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional

from app.domain.entities.product import Product


class IProductRepository(ABC):

    @abstractmethod
    async def find_by_id(self, product_id: int) -> Optional[Product]: ...

    @abstractmethod
    async def find_all_active(self) -> List[Product]: ...

    @abstractmethod
    async def find_all(self) -> List[Product]: ...

    @abstractmethod
    async def search(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort: Optional[str] = None,
    ) -> List[Product]: ...

    @abstractmethod
    async def save(self, product: Product) -> Product: ...

    @abstractmethod
    async def exists_by_sku(self, sku: str) -> bool: ...

    @abstractmethod
    async def count(self) -> int: ...

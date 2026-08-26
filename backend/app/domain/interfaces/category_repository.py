"""Abstract repository interface for Category entity."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.category import Category


class ICategoryRepository(ABC):

    @abstractmethod
    async def find_by_id(self, category_id: int) -> Optional[Category]: ...

    @abstractmethod
    async def find_all(self) -> List[Category]: ...

    @abstractmethod
    async def save(self, category: Category) -> Category: ...

    @abstractmethod
    async def delete(self, category: Category) -> None: ...

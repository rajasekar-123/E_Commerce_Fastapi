"""Abstract repository interface for Review entity."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.review import Review


class IReviewRepository(ABC):

    @abstractmethod
    async def find_by_product_id(self, product_id: int) -> List[Review]: ...

    @abstractmethod
    async def save(self, review: Review) -> Review: ...

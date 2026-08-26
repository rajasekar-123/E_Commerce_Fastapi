"""
Abstract repository interfaces for domain entities.

Following Interface Segregation Principle — one focused interface per entity.
High-level services depend on these abstractions, not concrete implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.user import User


class IUserRepository(ABC):
    """Repository interface for User entity operations."""

    @abstractmethod
    async def find_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    async def save(self, user: User) -> User: ...

    @abstractmethod
    async def find_all(self) -> List[User]: ...

    @abstractmethod
    async def count(self) -> int: ...

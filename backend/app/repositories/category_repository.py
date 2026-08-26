"""CategoryRepository."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, category_id: int) -> Optional[Category]:
        result = await self._session.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def find_all(self) -> List[Category]:
        result = await self._session.execute(
            select(Category).order_by(Category.name)
        )
        return list(result.scalars().all())

    async def save(self, category: Category) -> Category:
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def delete(self, category: Category) -> None:
        await self._session.delete(category)
        await self._session.flush()

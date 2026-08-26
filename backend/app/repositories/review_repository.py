"""ReviewRepository."""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.review import Review
from app.models.user import User


class ReviewRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_product_id(self, product_id: int) -> List[Review]:
        result = await self._session.execute(
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
        )
        return list(result.scalars().all())

    async def save(self, review: Review) -> Review:
        self._session.add(review)
        await self._session.flush()
        result = await self._session.execute(
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.id == review.id)
        )
        return result.scalar_one()

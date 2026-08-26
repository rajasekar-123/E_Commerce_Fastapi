"""
ProductRepository — with brand filter, pagination, and full-text search via LIKE.
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.product import Product


class ProductRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, product_id: int) -> Optional[Product]:
        result = await self._session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def find_all_active(self, skip: int = 0, limit: int = 50) -> List[Product]:
        result = await self._session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.is_active == True)  # noqa: E712
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_all(self, skip: int = 0, limit: int = 50) -> List[Product]:
        result = await self._session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        brand: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Product]:
        stmt = (
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.is_active == True)  # noqa: E712
        )

        if query and query.strip():
            like_pattern = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Product.name).like(like_pattern),
                    func.lower(Product.description).like(like_pattern),
                    func.lower(Product.brand).like(like_pattern),
                )
            )

        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if brand is not None:
            stmt = stmt.where(func.lower(Product.brand) == brand.lower())

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)

        if sort == "price_asc":
            stmt = stmt.order_by(Product.price.asc())
        elif sort == "price_desc":
            stmt = stmt.order_by(Product.price.desc())
        elif sort == "rating_desc":
            stmt = stmt.order_by(Product.rating.desc().nullslast())
        elif sort == "newest":
            stmt = stmt.order_by(Product.created_at.desc())
        else:
            stmt = stmt.order_by(Product.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, product: Product) -> Product:
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product)
        # Re-load with category
        result = await self._session.execute(
            select(Product)
            .options(selectinload(Product.category))
            .where(Product.id == product.id)
        )
        return result.scalar_one()

    async def exists_by_sku(self, sku: str) -> bool:
        result = await self._session.execute(
            select(func.count()).where(Product.sku == sku)
        )
        return result.scalar_one() > 0

    async def count_active(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Product).where(Product.is_active == True)  # noqa
        )
        return result.scalar_one()

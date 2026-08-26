"""OrderRepository — with pagination and payment relationship loading."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.address import Address
from app.models.payment import Payment


class OrderRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, order_id: int) -> Optional[Order]:
        result = await self._session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.shipping_address),
                selectinload(Order.user),
                selectinload(Order.payment),
            )
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def find_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Order]:
        result = await self._session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.shipping_address),
                selectinload(Order.payment),
            )
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_all(self, skip: int = 0, limit: int = 50) -> List[Order]:
        result = await self._session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.shipping_address),
                selectinload(Order.user),
                selectinload(Order.payment),
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def save(self, order: Order) -> Order:
        self._session.add(order)
        await self._session.flush()
        # Reload with full relationships
        result = await self._session.execute(
            select(Order)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product),
                selectinload(Order.shipping_address),
                selectinload(Order.user),
                selectinload(Order.payment),
            )
            .where(Order.id == order.id)
        )
        return result.scalar_one()

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(Order))
        return result.scalar_one()

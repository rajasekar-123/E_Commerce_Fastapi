"""
PaymentRepository — data access layer for Payment entity.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payment import Payment, PaymentStatus


class PaymentRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_id(self, payment_id: int) -> Optional[Payment]:
        result = await self._session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def find_by_order_id(self, order_id: int) -> Optional[Payment]:
        result = await self._session.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def find_by_stripe_session_id(self, session_id: str) -> Optional[Payment]:
        result = await self._session.execute(
            select(Payment).where(Payment.stripe_session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def find_by_stripe_payment_intent(self, intent_id: str) -> Optional[Payment]:
        result = await self._session.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == intent_id)
        )
        return result.scalar_one_or_none()

    async def webhook_event_processed(self, event_id: str) -> bool:
        """
        Check if a Stripe webhook event has already been processed.
        Used for idempotency — prevents duplicate order/payment updates.
        """
        result = await self._session.execute(
            select(Payment).where(Payment.stripe_webhook_event_id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def save(self, payment: Payment) -> Payment:
        self._session.add(payment)
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

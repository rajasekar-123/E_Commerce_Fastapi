"""
Payment entity — SQLAlchemy 2.x Mapped model.

Persists every payment attempt so payment state is always server-controlled.
Supports both Stripe (primary) and Razorpay (legacy compatibility).
Idempotency enforced via stripe_webhook_event_id unique constraint.
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Payment(Base):
    """
    Payment record — one per order (UNIQUE on order_id).

    The backend is the SOLE authority on payment status.
    Frontend values are NEVER trusted for status or amount.
    """

    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("stripe_webhook_event_id", name="uq_stripe_webhook_event"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Foreign keys
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # One payment per order
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    # Amount — always calculated server-side
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    # Status — only updated by webhook or internal service, never frontend
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )

    # Stripe fields (primary gateway)
    stripe_session_id: Mapped[Optional[str]] = mapped_column(
        String(500), unique=True, nullable=True
    )
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    stripe_webhook_event_id: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )  # Idempotency: unique constraint above prevents duplicate webhook processing

    # Razorpay fields (legacy / backward compat)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Payment method metadata
    payment_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payment")
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} order_id={self.order_id} status={self.status}>"

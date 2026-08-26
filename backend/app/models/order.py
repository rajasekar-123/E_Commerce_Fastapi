"""
Order and OrderStatus entities — SQLAlchemy 2.x Mapped models.

Enhanced with:
  - PaymentStatus enum (separate from order fulfillment status)
  - subtotal, tax, shipping_fee fields for accurate pricing breakdown
  - billing_address_id FK
  - payment relationship back to Payment entity
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.address import Address
    from app.models.order_item import OrderItem
    from app.models.payment import Payment


class OrderStatus(str, enum.Enum):
    """Order fulfilment lifecycle."""
    PENDING = "PENDING"             # Created, waiting for payment
    PAYMENT_PENDING = "PAYMENT_PENDING"   # Stripe session created, awaiting payment
    PAYMENT_FAILED = "PAYMENT_FAILED"     # Payment declined/expired
    CONFIRMED = "CONFIRMED"         # Payment received, seller confirmed
    PROCESSING = "PROCESSING"       # Being prepared
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, enum.Enum):
    """Payment state — controlled only by backend/webhook, NEVER by frontend."""
    UNPAID = "UNPAID"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class Order(Base):
    """
    Order entity.

    IMPORTANT: total_amount is always calculated server-side.
    Frontend prices are NEVER trusted.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="order_payment_status"),
        nullable=False,
        default=PaymentStatus.UNPAID,
        index=True,
    )

    # Price breakdown — all server-calculated
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    shipping_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    # FKs
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("addresses.id"))
    billing_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("addresses.id"))

    # Cancellation/refund reason
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    shipping_address: Mapped[Optional["Address"]] = relationship(
        "Address", foreign_keys=[address_id]
    )
    billing_address: Mapped[Optional["Address"]] = relationship(
        "Address", foreign_keys=[billing_address_id]
    )
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="select",
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="order", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status} payment_status={self.payment_status}>"

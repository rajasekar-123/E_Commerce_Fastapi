"""
User entity — SQLAlchemy 2.x Mapped model.
Mirrors Spring Boot User entity with MySQL → PostgreSQL migration.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.address import Address
    from app.models.review import Review
    from app.models.cart import Cart


class Role(str, enum.Enum):
    """User roles — mirrors Spring Boot Role enum."""
    USER = "USER"
    ADMIN = "ADMIN"


class User(Base):
    """
    User entity.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"), nullable=False, default=Role.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user", lazy="select")
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", lazy="select")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", lazy="select")
    cart: Mapped[Optional["Cart"]] = relationship("Cart", back_populates="user", uselist=False, lazy="select")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"

"""
CartRepository — data access layer for Cart and CartItem entities.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.product import Product


class CartRepository:

    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_by_user_id(self, user_id: int) -> Optional[Cart]:
        """Return the user's cart with all items and product details loaded."""
        result = await self._session.execute(
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.category)
            )
            .where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def find_cart_item(self, cart_id: int, product_id: int) -> Optional[CartItem]:
        """Find a specific item in the cart by product."""
        result = await self._session.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_cart_item_by_id(self, item_id: int) -> Optional[CartItem]:
        result = await self._session.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def save_cart(self, cart: Cart) -> Cart:
        self._session.add(cart)
        await self._session.flush()
        # Reload with full relationships
        result = await self._session.execute(
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product).selectinload(Product.category)
            )
            .where(Cart.id == cart.id)
        )
        return result.scalar_one()

    async def save_item(self, item: CartItem) -> CartItem:
        self._session.add(item)
        await self._session.flush()
        result = await self._session.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.id == item.id)
        )
        return result.scalar_one()

    async def delete_item(self, item: CartItem) -> None:
        await self._session.delete(item)
        await self._session.flush()

    async def clear_cart(self, cart: Cart) -> None:
        """Remove all items from the cart (used post-checkout)."""
        for item in cart.items:
            await self._session.delete(item)
        await self._session.flush()

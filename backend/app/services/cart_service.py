"""
Cart Service — business logic for shopping cart operations.

Rules enforced:
  - One cart per user (auto-created on first use)
  - Stock validation on add/update
  - Backend calculates all prices (never trusts frontend)
  - Cart is cleared after successful order placement
"""

from decimal import Decimal
from typing import List

from app.core.exceptions import BadRequestError, NotFoundError
from app.core.logging import get_logger
from app.models.cart import Cart, CartItem
from app.repositories.cart_repository import CartRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)

logger = get_logger(__name__)

TAX_RATE = Decimal("0.00")          # Set to e.g. Decimal("0.18") for 18% GST
FREE_SHIPPING_THRESHOLD = Decimal("999.00")
SHIPPING_FEE = Decimal("49.00")


class CartService:

    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository):
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    async def get_cart(self, user_id: int) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)
        return self._build_response(cart)

    async def add_item(self, user_id: int, request: CartItemCreate) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)

        product = await self._product_repo.find_by_id(request.product_id)
        if product is None or not product.is_active:
            raise NotFoundError(f"Product {request.product_id} not found")

        if product.stock < request.quantity:
            raise BadRequestError(
                f"Insufficient stock for '{product.name}'. "
                f"Available: {product.stock}"
            )

        # Check if product already in cart
        existing = await self._cart_repo.find_cart_item(cart.id, request.product_id)
        if existing:
            new_qty = existing.quantity + request.quantity
            if product.stock < new_qty:
                raise BadRequestError(
                    f"Cannot add {request.quantity} more of '{product.name}'. "
                    f"Only {product.stock - existing.quantity} additional units available."
                )
            existing.quantity = new_qty
            await self._cart_repo.save_item(existing)
            logger.info("Cart item quantity updated", user_id=user_id, product_id=request.product_id, qty=new_qty)
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=request.product_id,
                quantity=request.quantity,
            )
            await self._cart_repo.save_item(item)
            logger.info("Cart item added", user_id=user_id, product_id=request.product_id)

        # Reload cart
        cart = await self._cart_repo.find_by_user_id(user_id)
        return self._build_response(cart)

    async def update_item(self, user_id: int, item_id: int, request: CartItemUpdate) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)

        item = await self._cart_repo.find_cart_item_by_id(item_id)
        if item is None or item.cart_id != cart.id:
            raise NotFoundError(f"Cart item {item_id} not found")

        product = await self._product_repo.find_by_id(item.product_id)
        if product is None:
            raise NotFoundError("Product no longer available")

        if product.stock < request.quantity:
            raise BadRequestError(
                f"Insufficient stock. Available: {product.stock}"
            )

        item.quantity = request.quantity
        await self._cart_repo.save_item(item)

        cart = await self._cart_repo.find_by_user_id(user_id)
        return self._build_response(cart)

    async def remove_item(self, user_id: int, item_id: int) -> CartResponse:
        cart = await self._get_or_create_cart(user_id)

        item = await self._cart_repo.find_cart_item_by_id(item_id)
        if item is None or item.cart_id != cart.id:
            raise NotFoundError(f"Cart item {item_id} not found")

        await self._cart_repo.delete_item(item)
        logger.info("Cart item removed", user_id=user_id, item_id=item_id)

        cart = await self._cart_repo.find_by_user_id(user_id)
        return self._build_response(cart)

    async def clear_cart(self, user_id: int) -> None:
        cart = await self._cart_repo.find_by_user_id(user_id)
        if cart:
            await self._cart_repo.clear_cart(cart)
            logger.info("Cart cleared", user_id=user_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_or_create_cart(self, user_id: int) -> Cart:
        cart = await self._cart_repo.find_by_user_id(user_id)
        if cart is None:
            cart = Cart(user_id=user_id)
            cart = await self._cart_repo.save_cart(cart)
            logger.info("Cart created", user_id=user_id)
        return cart

    @staticmethod
    def _effective_price(product) -> Decimal:
        """Return the effective (discounted or regular) price."""
        if product.discount_price and product.discount_price < product.price:
            return product.discount_price
        return product.price

    def _build_response(self, cart: Cart) -> CartResponse:
        item_responses: List[CartItemResponse] = []
        subtotal = Decimal("0.00")
        total_discount = Decimal("0.00")

        for item in (cart.items or []):
            p = item.product
            if p is None:
                continue

            unit_price = self._effective_price(p)
            original_price = p.price
            item_subtotal = unit_price * item.quantity
            item_discount = (original_price - unit_price) * item.quantity

            subtotal += item_subtotal
            total_discount += item_discount

            item_responses.append(CartItemResponse(
                id=item.id,
                product_id=p.id,
                product_name=p.name,
                product_image=p.image_url,
                product_brand=getattr(p, "brand", None),
                unit_price=unit_price,
                original_price=original_price,
                quantity=item.quantity,
                subtotal=item_subtotal,
                in_stock=p.stock > 0,
                available_stock=p.stock,
                added_at=item.added_at,
            ))

        total = subtotal  # tax applied at checkout if needed

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=item_responses,
            item_count=sum(i.quantity for i in (cart.items or [])),
            subtotal=subtotal,
            total_discount=total_discount,
            total=total,
        )

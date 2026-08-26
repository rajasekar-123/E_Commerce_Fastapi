"""
AI Tool Service — structured tools the LLM can invoke.

SECURITY RULES:
  - get_user_orders / get_order_details always require user_id — AI cannot access other users' data
  - add_to_cart requires user_id — AI adds on user's behalf, not blindly
  - AI can NEVER initiate checkout or payment — only cart manipulation is allowed
  - compare_products gives structured data for side-by-side comparison
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.repositories.cart_repository import CartRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository

logger = get_logger(__name__)


class ToolService:

    def __init__(
        self,
        product_repo: ProductRepository,
        order_repo: OrderRepository,
        category_repo: CategoryRepository,
        cart_repo: CartRepository,
    ):
        self._product_repo = product_repo
        self._order_repo = order_repo
        self._category_repo = category_repo
        self._cart_repo = cart_repo

    # ── Product tools ─────────────────────────────────────────────────────────

    async def search_products(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        brand: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        sort: Optional[str] = "rating_desc",
        max_results: int = 6,
    ) -> List[Dict[str, Any]]:
        logger.info("AI tool: search_products", query=query, category_id=category_id, brand=brand)
        products = await self._product_repo.search(
            query=query,
            category_id=category_id,
            brand=brand,
            min_price=Decimal(str(min_price)) if min_price else None,
            max_price=Decimal(str(max_price)) if max_price else None,
            sort=sort,
            limit=max_results,
        )
        return [self._product_to_dict(p) for p in products]

    async def get_product_details(self, product_id: int) -> Dict[str, Any]:
        logger.info("AI tool: get_product_details", product_id=product_id)
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return self._product_to_dict(product, full=True)

    async def compare_products(self, product_ids: List[int]) -> List[Dict[str, Any]]:
        """Compare multiple products side-by-side."""
        logger.info("AI tool: compare_products", product_ids=product_ids)
        if len(product_ids) > 5:
            raise BadRequestError("Cannot compare more than 5 products at once")
        results = []
        for pid in product_ids:
            product = await self._product_repo.find_by_id(pid)
            if product:
                results.append(self._product_to_dict(product, full=True))
        return results

    async def get_categories(self) -> List[Dict[str, Any]]:
        logger.info("AI tool: get_categories")
        categories = await self._category_repo.find_all()
        return [{"id": c.id, "name": c.name, "description": c.description} for c in categories]

    # ── Order tools ───────────────────────────────────────────────────────────

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get a user's recent orders — user_id ensures data isolation."""
        logger.info("AI tool: get_user_orders", user_id=user_id)
        orders = await self._order_repo.find_by_user_id(user_id, limit=10)
        return [self._order_to_dict(o) for o in orders]

    async def get_order_details(self, order_id: int, user_id: int) -> Dict[str, Any]:
        """Get order details — enforces ownership check."""
        logger.info("AI tool: get_order_details", order_id=order_id, user_id=user_id)
        order = await self._order_repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenError("You do not have access to this order")
        return self._order_to_dict(order, full=True)

    # ── Cart tools ────────────────────────────────────────────────────────────

    async def view_cart(self, user_id: int) -> Dict[str, Any]:
        """Return a summary of the user's current cart."""
        logger.info("AI tool: view_cart", user_id=user_id)
        cart = await self._cart_repo.find_by_user_id(user_id)
        if cart is None:
            return {"items": [], "item_count": 0, "total": "0.00"}

        items = []
        total = Decimal("0.00")
        for item in cart.items:
            p = item.product
            if not p:
                continue
            price = p.discount_price if p.discount_price and p.discount_price < p.price else p.price
            subtotal = price * item.quantity
            total += subtotal
            items.append({
                "cart_item_id": item.id,
                "product_id": p.id,
                "product_name": p.name,
                "quantity": item.quantity,
                "unit_price": float(price),
                "subtotal": float(subtotal),
            })

        return {
            "cart_id": cart.id,
            "items": items,
            "item_count": sum(i["quantity"] for i in items),
            "total": float(total),
        }

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Dict[str, Any]:
        """
        Add a product to the cart on behalf of the user.

        SECURITY: AI can only add, never checkout or charge.
        Returns a confirmation so the LLM can relay it to the user.
        """
        logger.info("AI tool: add_to_cart", user_id=user_id, product_id=product_id, qty=quantity)
        product = await self._product_repo.find_by_id(product_id)
        if product is None or not product.is_active:
            raise NotFoundError(f"Product {product_id} not found")
        if product.stock < quantity:
            raise BadRequestError(
                f"Only {product.stock} units of '{product.name}' are available."
            )

        from app.models.cart import Cart, CartItem
        from sqlalchemy import select

        cart = await self._cart_repo.find_by_user_id(user_id)
        if cart is None:
            cart = Cart(user_id=user_id)
            cart = await self._cart_repo.save_cart(cart)

        existing = await self._cart_repo.find_cart_item(cart.id, product_id)
        if existing:
            new_qty = existing.quantity + quantity
            if product.stock < new_qty:
                raise BadRequestError(
                    f"Cannot add {quantity} more — only {product.stock - existing.quantity} additional units available."
                )
            existing.quantity = new_qty
            await self._cart_repo.save_item(existing)
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            await self._cart_repo.save_item(item)

        return {
            "status": "added",
            "product_name": product.name,
            "quantity_added": quantity,
            "message": f"✅ Added {quantity}× '{product.name}' to your cart.",
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _product_to_dict(product, full: bool = False) -> Dict[str, Any]:
        effective_price = (
            float(product.discount_price)
            if product.discount_price and product.discount_price < product.price
            else float(product.price)
        )
        data = {
            "id": product.id,
            "name": product.name,
            "brand": getattr(product, "brand", None),
            "price": float(product.price),
            "effective_price": effective_price,
            "discount_price": float(product.discount_price) if product.discount_price else None,
            "stock": product.stock,
            "in_stock": product.stock > 0,
            "rating": product.rating,
            "review_count": product.review_count,
            "category": product.category.name if product.category else None,
        }
        if full:
            data["description"] = product.description or ""
            data["sku"] = product.sku
            data["image_url"] = product.image_url
        return data

    @staticmethod
    def _order_to_dict(order, full: bool = False) -> Dict[str, Any]:
        data = {
            "id": order.id,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "total_amount": float(order.total_amount),
            "created_at": order.created_at.isoformat(),
            "item_count": len(order.items),
        }
        if full:
            data["items"] = [
                {
                    "product_name": item.product.name if item.product else "Unknown",
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "subtotal": float(item.price * item.quantity),
                }
                for item in order.items
            ]
            data["shipping_address"] = {
                "address_line1": order.shipping_address.address_line1 if order.shipping_address else None,
                "city": order.shipping_address.city if order.shipping_address else None,
                "state": order.shipping_address.state if order.shipping_address else None,
            } if order.shipping_address else None
        return data

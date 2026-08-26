"""
AI Tool Service — allows the LLM to access live e-commerce data from PostgreSQL.

Security: All tools verify the current user's permissions before returning data.
The LLM CANNOT bypass authorization through tool calls.

Tools available:
  - search_products(query, category_id, user)  → public product data
  - get_product_details(product_id)            → public product data
  - get_categories()                           → public category data
  - get_user_orders(user)                      → user's own orders only
  - get_order_details(order_id, user)          → verifies ownership
"""

from typing import Any, Dict, List, Optional

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.domain.interfaces.category_repository import ICategoryRepository
from app.domain.interfaces.order_repository import IOrderRepository
from app.domain.interfaces.product_repository import IProductRepository

logger = get_logger(__name__)


class ToolService:
    """
    Provides structured data access tools for the AI assistant.
    Each tool enforces authorization before returning data.
    """

    def __init__(
        self,
        product_repo: IProductRepository,
        order_repo: IOrderRepository,
        category_repo: ICategoryRepository,
    ):
        self._product_repo = product_repo
        self._order_repo = order_repo
        self._category_repo = category_repo

    async def search_products(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search products — public data, no authorization required.
        Returns a simplified dict for LLM consumption.
        """
        logger.info("AI tool: search_products", query=query, category_id=category_id)
        products = await self._product_repo.search(query=query, category_id=category_id)
        results = []
        for p in products[:max_results]:
            results.append({
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "discount_price": float(p.discount_price) if p.discount_price else None,
                "stock": p.stock,
                "rating": p.rating,
                "review_count": p.review_count,
                "description": (p.description or "")[:300],  # truncate for LLM context
            })
        return results

    async def get_product_details(self, product_id: int) -> Dict[str, Any]:
        """Get detailed product information — public data."""
        logger.info("AI tool: get_product_details", product_id=product_id)
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product {product_id} not found")
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "discount_price": float(product.discount_price) if product.discount_price else None,
            "stock": product.stock,
            "rating": product.rating,
            "review_count": product.review_count,
            "category": product.category.name if product.category else None,
            "sku": product.sku,
        }

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories — public data."""
        logger.info("AI tool: get_categories")
        categories = await self._category_repo.find_all()
        return [{"id": c.id, "name": c.name, "description": c.description} for c in categories]

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get a user's orders.
        Security: only returns orders belonging to user_id.
        """
        logger.info("AI tool: get_user_orders", user_id=user_id)
        orders = await self._order_repo.find_by_user_id(user_id)
        results = []
        for order in orders[:10]:  # limit for LLM context
            results.append({
                "id": order.id,
                "status": order.status.value,
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat(),
                "item_count": len(order.items),
                "items": [
                    {
                        "product_name": item.product.name if item.product else "Unknown",
                        "quantity": item.quantity,
                        "price": float(item.price),
                    }
                    for item in order.items
                ],
            })
        return results

    async def get_order_details(self, order_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get order details with ownership verification.
        Security: raises ForbiddenError if user does not own this order.
        """
        logger.info("AI tool: get_order_details", order_id=order_id, user_id=user_id)
        order = await self._order_repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")

        # Authorization: verify ownership
        if order.user_id != user_id:
            raise ForbiddenError("You do not have access to this order")

        return {
            "id": order.id,
            "status": order.status.value,
            "total_amount": float(order.total_amount),
            "created_at": order.created_at.isoformat(),
            "shipping_address": {
                "address_line1": order.shipping_address.address_line1 if order.shipping_address else None,
                "city": order.shipping_address.city if order.shipping_address else None,
                "state": order.shipping_address.state if order.shipping_address else None,
                "country": order.shipping_address.country if order.shipping_address else None,
            } if order.shipping_address else None,
            "items": [
                {
                    "product_name": item.product.name if item.product else "Unknown",
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "subtotal": float(item.price * item.quantity),
                }
                for item in order.items
            ],
        }

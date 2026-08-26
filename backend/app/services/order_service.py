"""
Order Service — business logic for order lifecycle.

FIXES applied:
  1. Order creation is wrapped in a SELECT FOR UPDATE transaction to prevent overselling
  2. Email confirmation properly passed through background tasks
  3. PaymentStatus/OrderStatus enums use new expanded set
  4. Ownership is enforced at service level (not just route level)
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.repositories.address_repository import AddressRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.address import AddressResponse
from app.schemas.order import OrderCreate, OrderItemResponse, OrderResponse

logger = get_logger(__name__)

# Tax / shipping constants
TAX_RATE = Decimal("0.00")
FREE_SHIPPING_THRESHOLD = Decimal("999.00")
SHIPPING_FEE = Decimal("49.00")


class OrderService:

    def __init__(
        self,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        product_repo: ProductRepository,
        address_repo: AddressRepository,
        email_service,
        db_session: AsyncSession,
    ):
        self._order_repo = order_repo
        self._user_repo = user_repo
        self._product_repo = product_repo
        self._address_repo = address_repo
        self._email_service = email_service
        self._db = db_session

    async def get_user_orders(self, user_id: int, skip: int = 0, limit: int = 20) -> List[OrderResponse]:
        orders = await self._order_repo.find_by_user_id(user_id, skip=skip, limit=limit)
        return [self._map_to_response(o) for o in orders]

    async def get_all_orders(self, skip: int = 0, limit: int = 50) -> List[OrderResponse]:
        orders = await self._order_repo.find_all(skip=skip, limit=limit)
        return [self._map_to_response(o) for o in orders]

    async def get_by_id(self, order_id: int, requesting_user_id: int, is_admin: bool = False) -> OrderResponse:
        """
        Get order by ID with ownership check.

        SECURITY FIX: Any user can only see their own orders unless they're admin.
        """
        order = await self._order_repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")

        if not is_admin and order.user_id != requesting_user_id:
            raise ForbiddenError("You do not have access to this order")

        return self._map_to_response(order)

    async def create_order(self, user_id: int, request: OrderCreate) -> Order:
        """
        Create an order from a list of items.

        TRANSACTION SAFETY:
          - Product stock is locked with SELECT FOR UPDATE
          - Stock decrement and order creation happen in the same DB transaction
          - The get_db() session commits/rolls back atomically

        Returns the raw Order model (not DTO) so the route can pass it to email.
        """
        address = await self._address_repo.find_by_id(request.address_id)
        if address is None:
            raise NotFoundError(f"Address {request.address_id} not found")
        if address.user_id != user_id:
            raise ForbiddenError("You do not have access to this address")

        user = await self._user_repo.find_by_id(user_id)

        # Build order
        order = Order(
            user_id=user_id,
            address_id=request.address_id,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.UNPAID,
        )
        order.user = user  # Explicitly assign to prevent lazy load in background task

        items = []
        subtotal = Decimal("0.00")

        for item_req in request.items:
            # Lock product row to prevent concurrent oversell
            result = await self._db.execute(
                select(Product)
                .where(Product.id == item_req.product_id)
                .with_for_update()
            )
            product = result.scalar_one_or_none()

            if product is None or not product.is_active:
                raise NotFoundError(f"Product {item_req.product_id} not found")

            if product.stock < item_req.quantity:
                raise BadRequestError(
                    f"Insufficient stock for '{product.name}'. "
                    f"Available: {product.stock}, Requested: {item_req.quantity}"
                )

            # Deduct stock — inside the same transaction
            product.stock -= item_req.quantity
            self._db.add(product)

            # Price snapshot — always from DB, never from frontend
            price = (
                product.discount_price
                if product.discount_price and product.discount_price < product.price
                else product.price
            )

            order_item = OrderItem(
                product_id=product.id,
                quantity=item_req.quantity,
                price=price,
            )
            order_item.product = product  # Explicitly assign to prevent lazy load
            items.append(order_item)
            subtotal += price * item_req.quantity

        # Compute totals server-side
        tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
        shipping = Decimal("0.00") if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE
        total = subtotal + tax + shipping

        order.subtotal = subtotal
        order.tax = tax
        order.shipping_fee = shipping
        order.total_amount = total
        order.items = items

        saved_order = await self._order_repo.save(order)
        logger.info(
            "Order created",
            order_id=saved_order.id,
            user_id=user_id,
            total=str(total),
        )
        return saved_order

    async def update_status(self, order_id: int, new_status: str) -> OrderResponse:
        order = await self._order_repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        order.status = OrderStatus(new_status)
        saved = await self._order_repo.save(order)
        return self._map_to_response(saved)

    async def count_orders(self) -> int:
        return await self._order_repo.count()

    async def get_total_revenue(self) -> Decimal:
        from sqlalchemy import select, func as sqlfunc
        from app.models.order import Order as OrderModel, PaymentStatus as PayStatus
        result = await self._db.execute(
            select(sqlfunc.coalesce(sqlfunc.sum(OrderModel.total_amount), Decimal("0.00")))
            .where(OrderModel.payment_status == PayStatus.PAID)
        )
        return result.scalar_one() or Decimal("0.00")

    async def cancel_order(self, order_id: int, user_id: int, reason: Optional[str] = None) -> OrderResponse:
        order = await self._order_repo.find_by_id(order_id)
        if order is None:
            raise NotFoundError(f"Order {order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenError("Access denied")

        cancellable = {OrderStatus.PENDING, OrderStatus.PAYMENT_PENDING, OrderStatus.PAYMENT_FAILED}
        if order.status not in cancellable:
            raise BadRequestError(
                f"Cannot cancel order with status '{order.status.value}'. "
                "Only pending or payment-failed orders can be cancelled."
            )

        order.status = OrderStatus.CANCELLED
        if reason:
            order.cancellation_reason = reason

        # Restore stock if payment not made
        if order.payment_status == PaymentStatus.UNPAID:
            for item in order.items:
                result = await self._db.execute(
                    select(Product).where(Product.id == item.product_id).with_for_update()
                )
                product = result.scalar_one_or_none()
                if product:
                    product.stock += item.quantity
                    self._db.add(product)

        saved = await self._order_repo.save(order)
        logger.info("Order cancelled", order_id=order_id, user_id=user_id)
        return self._map_to_response(saved)

    def _map_to_response(self, order: Order) -> OrderResponse:
        address_response = None
        if order.shipping_address:
            address_response = AddressResponse.model_validate(order.shipping_address)

        items = [
            OrderItemResponse(
                product_id=item.product_id,
                product_name=item.product.name if item.product else "",
                image_url=item.product.image_url if item.product else None,
                quantity=item.quantity,
                price=item.price,
                subtotal=item.price * item.quantity,
            )
            for item in order.items
        ]

        return OrderResponse(
            id=order.id,
            status=order.status.value,
            payment_status=order.payment_status.value,
            subtotal=order.subtotal,
            tax=order.tax,
            shipping_fee=order.shipping_fee,
            total_amount=order.total_amount,
            shipping_address=address_response,
            items=items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

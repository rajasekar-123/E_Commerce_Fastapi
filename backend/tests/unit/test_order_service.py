"""Unit tests for OrderService — business rules."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.order_service import OrderService
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.address import Address
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate, OrderItemCreate


def make_product(stock: int = 10, price: Decimal = Decimal("100.00"), discount_price=None) -> Product:
    p = Product()
    p.id = 1
    p.name = "Test Product"
    p.stock = stock
    p.price = price
    p.discount_price = discount_price
    p.image_url = None
    return p


def make_address() -> Address:
    a = Address()
    a.id = 1
    a.address_line1 = "123 Main St"
    a.city = "Chennai"
    a.state = "TN"
    a.postal_code = "600001"
    a.country = "India"
    return a


def make_order(items=None) -> Order:
    o = Order()
    o.id = 1
    o.status = OrderStatus.PENDING
    o.total_amount = Decimal("200.00")
    o.user = User()
    o.user.id = 1
    o.user.email = "test@example.com"
    o.user.first_name = "Test"
    o.user.last_name = "User"
    o.shipping_address = make_address()
    o.items = items or []
    o.created_at = __import__("datetime").datetime.now()
    return o


def make_service(order_repo, user_repo, product_repo, address_repo, email_service):
    return OrderService(
        order_repo=order_repo,
        user_repo=user_repo,
        product_repo=product_repo,
        address_repo=address_repo,
        email_service=email_service,
    )


@pytest.mark.asyncio
async def test_create_order_deducts_stock(
    mock_order_repo, mock_product_repo, mock_address_repo, mock_email_service
):
    """Business rule: stock is deducted on order creation."""
    product = make_product(stock=10)
    mock_product_repo.find_by_id.return_value = product
    mock_product_repo.save.return_value = product
    mock_address_repo.find_by_id.return_value = make_address()
    saved_order = make_order()
    mock_order_repo.save.return_value = saved_order

    service = make_service(
        mock_order_repo, AsyncMock(), mock_product_repo, mock_address_repo, mock_email_service
    )

    await service.create_order(
        user_id=1,
        request=OrderCreate(address_id=1, items=[OrderItemCreate(product_id=1, quantity=3)]),
    )

    assert product.stock == 7  # deducted from 10


@pytest.mark.asyncio
async def test_create_order_raises_on_insufficient_stock(
    mock_order_repo, mock_product_repo, mock_address_repo, mock_email_service
):
    """Business rule: raise 400 if stock < requested quantity."""
    product = make_product(stock=2)
    mock_product_repo.find_by_id.return_value = product
    mock_address_repo.find_by_id.return_value = make_address()

    service = make_service(
        mock_order_repo, AsyncMock(), mock_product_repo, mock_address_repo, mock_email_service
    )

    with pytest.raises(BadRequestError, match="Insufficient stock"):
        await service.create_order(
            user_id=1,
            request=OrderCreate(address_id=1, items=[OrderItemCreate(product_id=1, quantity=5)]),
        )


@pytest.mark.asyncio
async def test_create_order_uses_discount_price(
    mock_order_repo, mock_product_repo, mock_address_repo, mock_email_service
):
    """Business rule: use discount_price if set, else regular price."""
    product = make_product(stock=10, price=Decimal("100.00"), discount_price=Decimal("80.00"))
    mock_product_repo.find_by_id.return_value = product
    mock_product_repo.save.return_value = product
    mock_address_repo.find_by_id.return_value = make_address()

    captured_items = []

    async def capture_save(order):
        captured_items.extend(order.items)
        saved = make_order(items=order.items)
        return saved

    mock_order_repo.save.side_effect = capture_save

    service = make_service(
        mock_order_repo, AsyncMock(), mock_product_repo, mock_address_repo, mock_email_service
    )
    await service.create_order(
        user_id=1,
        request=OrderCreate(address_id=1, items=[OrderItemCreate(product_id=1, quantity=1)]),
    )

    # Verify discount price was used
    assert captured_items[0].price == Decimal("80.00")


@pytest.mark.asyncio
async def test_update_status_raises_not_found(mock_order_repo, mock_product_repo, mock_address_repo, mock_email_service):
    mock_order_repo.find_by_id.return_value = None
    service = make_service(mock_order_repo, AsyncMock(), mock_product_repo, mock_address_repo, mock_email_service)

    with pytest.raises(NotFoundError):
        await service.update_status(999, "SHIPPED")

"""Admin routes."""

from typing import List

from fastapi import APIRouter, Depends

from app.api.dependencies import get_category_service, get_order_service, get_product_service
from app.core.security import require_admin
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.order import OrderResponse, OrderStatusUpdate
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
    summary="Create a new category",
)
async def create_category(
    request: CategoryCreate,
    category_service=Depends(get_category_service),
) -> CategoryResponse:
    return await category_service.create(request)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_admin)],
    summary="Update a category",
)
async def update_category(
    category_id: int,
    request: CategoryUpdate,
    category_service=Depends(get_category_service),
) -> CategoryResponse:
    return await category_service.update(category_id, request)


@router.delete(
    "/categories/{category_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
    summary="Delete a category",
)
async def delete_category(
    category_id: int,
    category_service=Depends(get_category_service),
) -> None:
    await category_service.delete(category_id)


@router.post(
    "/products",
    response_model=ProductResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
    summary="Create a new product",
)
async def create_product(
    request: ProductCreate,
    product_service=Depends(get_product_service),
) -> ProductResponse:
    return await product_service.create(request)


@router.put(
    "/products/{product_id}",
    response_model=ProductResponse,
    dependencies=[Depends(require_admin)],
    summary="Update a product",
)
async def update_product(
    product_id: int,
    request: ProductUpdate,
    product_service=Depends(get_product_service),
) -> ProductResponse:
    return await product_service.update(product_id, request)


@router.delete(
    "/products/{product_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
    summary="Soft-delete a product (sets is_active=False)",
)
async def delete_product(
    product_id: int,
    product_service=Depends(get_product_service),
) -> None:
    await product_service.soft_delete(product_id)


@router.get(
    "/orders",
    response_model=List[OrderResponse],
    dependencies=[Depends(require_admin)],
    summary="List all orders (admin view)",
)
async def get_all_orders(
    order_service=Depends(get_order_service),
) -> List[OrderResponse]:
    return await order_service.get_all_orders()


@router.put(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
    dependencies=[Depends(require_admin)],
    summary="Update order status",
)
async def update_order_status(
    order_id: int,
    request: OrderStatusUpdate,
    order_service=Depends(get_order_service),
) -> OrderResponse:
    return await order_service.update_status(order_id, request.status)


@router.get(
    "/dashboard",
    dependencies=[Depends(require_admin)],
    summary="Admin dashboard statistics",
)
async def get_dashboard(
    order_service=Depends(get_order_service),
    product_service=Depends(get_product_service),
) -> dict:
    # Use COUNT queries instead of fetching all rows
    total_orders = await order_service.count_orders()
    total_products = await product_service.count_products()
    total_revenue = await order_service.get_total_revenue()
    return {
        "totalOrders": total_orders,
        "totalProducts": total_products,
        "totalRevenue": str(total_revenue),
    }

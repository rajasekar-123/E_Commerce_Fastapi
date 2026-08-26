"""Order routes — with ownership enforcement and pagination."""

from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from app.api.dependencies import get_order_service
from app.core.security import get_current_user
from app.models.user import Role
from app.schemas.order import OrderCancelRequest, OrderCreate, OrderResponse

router = APIRouter()


@router.get(
    "",
    response_model=List[OrderResponse],
    summary="Get current user's orders",
)
async def get_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    order_service=Depends(get_order_service),
) -> List[OrderResponse]:
    return await order_service.get_user_orders(current_user.id, skip=skip, limit=limit)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order by ID (only your own orders)",
)
async def get_order_by_id(
    order_id: int,
    current_user=Depends(get_current_user),
    order_service=Depends(get_order_service),
) -> OrderResponse:
    # SECURITY FIX: ownership enforced — admin can see all, users only their own
    is_admin = current_user.role == Role.ADMIN
    return await order_service.get_by_id(
        order_id=order_id,
        requesting_user_id=current_user.id,
        is_admin=is_admin,
    )


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    summary="Create a new order from items list",
)
async def create_order(
    request: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    order_service=Depends(get_order_service),
) -> OrderResponse:
    order = await order_service.create_order(current_user.id, request)

    # Send confirmation email as a background task — passes order directly (no global state)
    background_tasks.add_task(
        order_service._email_service.send_order_confirmation,
        order,
    )

    return order_service._map_to_response(order)


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    summary="Cancel an order (only PENDING or PAYMENT_PENDING orders)",
)
async def cancel_order(
    order_id: int,
    request: OrderCancelRequest,
    current_user=Depends(get_current_user),
    order_service=Depends(get_order_service),
) -> OrderResponse:
    return await order_service.cancel_order(
        order_id=order_id,
        user_id=current_user.id,
        reason=request.reason,
    )

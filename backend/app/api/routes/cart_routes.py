"""Cart routes — full CRUD for the authenticated user's shopping cart."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_cart_service
from app.core.security import get_current_user
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse

router = APIRouter()


@router.get(
    "",
    response_model=CartResponse,
    summary="Get current user's cart (auto-created if not exists)",
)
async def get_cart(
    current_user=Depends(get_current_user),
    cart_service=Depends(get_cart_service),
) -> CartResponse:
    return await cart_service.get_cart(current_user.id)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=201,
    summary="Add a product to the cart",
)
async def add_item(
    request: CartItemCreate,
    current_user=Depends(get_current_user),
    cart_service=Depends(get_cart_service),
) -> CartResponse:
    return await cart_service.add_item(current_user.id, request)


@router.put(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Update quantity of a cart item",
)
async def update_item(
    item_id: int,
    request: CartItemUpdate,
    current_user=Depends(get_current_user),
    cart_service=Depends(get_cart_service),
) -> CartResponse:
    return await cart_service.update_item(current_user.id, item_id, request)


@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Remove a specific item from the cart",
)
async def remove_item(
    item_id: int,
    current_user=Depends(get_current_user),
    cart_service=Depends(get_cart_service),
) -> CartResponse:
    return await cart_service.remove_item(current_user.id, item_id)


@router.delete(
    "",
    status_code=204,
    summary="Clear all items from the cart",
)
async def clear_cart(
    current_user=Depends(get_current_user),
    cart_service=Depends(get_cart_service),
) -> None:
    await cart_service.clear_cart(current_user.id)

"""Review routes."""

from typing import List
from fastapi import APIRouter, Depends

from app.api.dependencies import get_review_service
from app.core.security import get_current_user
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()


@router.get(
    "/{product_id}/reviews",
    response_model=List[ReviewResponse],
    summary="Get all reviews for a product",
)
async def get_reviews(
    product_id: int,
    review_service=Depends(get_review_service),
) -> List[ReviewResponse]:
    return await review_service.get_product_reviews(product_id)


@router.post(
    "/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=201,
    summary="Add a review for a product",
)
async def add_review(
    product_id: int,
    request: ReviewCreate,
    current_user=Depends(get_current_user),
    review_service=Depends(get_review_service),
) -> ReviewResponse:
    return await review_service.add_review(current_user.id, product_id, request)

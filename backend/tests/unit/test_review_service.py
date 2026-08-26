"""Unit tests for ReviewService — business rule: rating recalculation."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock
from datetime import datetime

from app.services.review_service import ReviewService
from app.core.exceptions import NotFoundError
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewCreate


def make_product(rating=None, review_count=0) -> Product:
    p = Product()
    p.id = 1
    p.name = "Test Product"
    p.price = Decimal("100.00")
    p.stock = 10
    p.rating = rating
    p.review_count = review_count
    p.is_active = True
    return p


def make_review(rating: int, user_id: int = 1) -> Review:
    r = Review()
    r.id = 1
    r.product_id = 1
    r.rating = rating
    r.comment = "Test comment"
    r.created_at = datetime.now()
    u = User()
    u.first_name = "Test"
    u.last_name = "User"
    r.user = u
    r.user_id = user_id
    return r


@pytest.mark.asyncio
async def test_add_review_updates_product_rating(mock_review_repo, mock_product_repo, mock_user_repo):
    """Business rule: product rating recalculated after review submission."""
    product = make_product()
    mock_product_repo.find_by_id.return_value = product

    saved_review = make_review(rating=4)
    mock_review_repo.save.return_value = saved_review

    # Simulate 3 existing reviews + the new one
    existing_reviews = [make_review(4), make_review(5), make_review(3)]
    mock_review_repo.find_by_product_id.return_value = existing_reviews
    mock_product_repo.save.return_value = product

    service = ReviewService(mock_review_repo, mock_product_repo, mock_user_repo)
    await service.add_review(user_id=1, product_id=1, data=ReviewCreate(rating=4))

    # avg of [4, 5, 3] = 4.0
    assert product.rating == 4.0
    assert product.review_count == 3


@pytest.mark.asyncio
async def test_add_review_raises_not_found_for_missing_product(
    mock_review_repo, mock_product_repo, mock_user_repo
):
    mock_product_repo.find_by_id.return_value = None
    service = ReviewService(mock_review_repo, mock_product_repo, mock_user_repo)

    with pytest.raises(NotFoundError):
        await service.add_review(user_id=1, product_id=999, data=ReviewCreate(rating=5))


@pytest.mark.asyncio
async def test_rating_rounds_to_one_decimal(mock_review_repo, mock_product_repo, mock_user_repo):
    """Business rule: rating is rounded to 1 decimal place (mirrors Java Math.round(avg*10)/10)."""
    product = make_product()
    mock_product_repo.find_by_id.return_value = product
    saved_review = make_review(rating=4)
    mock_review_repo.save.return_value = saved_review

    reviews = [make_review(4), make_review(4), make_review(5)]  # avg = 4.333...
    mock_review_repo.find_by_product_id.return_value = reviews
    mock_product_repo.save.return_value = product

    service = ReviewService(mock_review_repo, mock_product_repo, mock_user_repo)
    await service.add_review(user_id=1, product_id=1, data=ReviewCreate(rating=4))

    assert product.rating == 4.3  # rounded to 1 decimal

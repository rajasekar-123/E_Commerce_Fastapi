"""Review Service."""

from typing import List

from app.core.exceptions import NotFoundError
from app.models.review import Review
from app.repositories.product_repository import ProductRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.schemas.review import ReviewCreate, ReviewResponse


class ReviewService:

    def __init__(
        self,
        review_repo: ReviewRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository,
    ):
        self._review_repo = review_repo
        self._product_repo = product_repo
        self._user_repo = user_repo

    async def get_product_reviews(self, product_id: int) -> List[ReviewResponse]:
        reviews = await self._review_repo.find_by_product_id(product_id)
        return [self._map_to_response(r) for r in reviews]

    async def add_review(
        self,
        user_id: int,
        product_id: int,
        data: ReviewCreate,
    ) -> ReviewResponse:
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product with id={product_id} not found")

        review = Review(
            user_id=user_id,
            product_id=product_id,
            rating=data.rating,
            comment=data.comment,
        )
        saved_review = await self._review_repo.save(review)

        await self._update_product_rating(product_id)

        return self._map_to_response(saved_review)

    async def _update_product_rating(self, product_id: int) -> None:
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            return

        all_reviews = await self._review_repo.find_by_product_id(product_id)
        if all_reviews:
            avg = sum(r.rating for r in all_reviews) / len(all_reviews)
            product.rating = round(avg, 1)
            product.review_count = len(all_reviews)
        else:
            product.rating = None
            product.review_count = 0

        await self._product_repo.save(product)

    def _map_to_response(self, review: Review) -> ReviewResponse:
        user_name = ""
        if review.user:
            user_name = f"{review.user.first_name or ''} {review.user.last_name or ''}".strip()
        return ReviewResponse(
            id=review.id,
            product_id=review.product_id,
            user_name=user_name,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )

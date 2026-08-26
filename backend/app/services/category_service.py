"""Category Service — CRUD business logic."""

from typing import List

from app.core.exceptions import NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate


class CategoryService:

    def __init__(self, category_repo: CategoryRepository):
        self._category_repo = category_repo

    async def get_all(self) -> List[CategoryResponse]:
        categories = await self._category_repo.find_all()
        return [CategoryResponse.model_validate(c) for c in categories]

    async def get_by_id(self, category_id: int) -> CategoryResponse:
        category = await self._category_repo.find_by_id(category_id)
        if category is None:
            raise NotFoundError(f"Category with id={category_id} not found")
        return CategoryResponse.model_validate(category)

    async def create(self, data: CategoryCreate) -> CategoryResponse:
        category = Category(
            name=data.name,
            description=data.description,
            image_url=data.image_url,
            is_active=data.is_active,
        )
        saved = await self._category_repo.save(category)
        return CategoryResponse.model_validate(saved)

    async def update(self, category_id: int, data: CategoryUpdate) -> CategoryResponse:
        category = await self._category_repo.find_by_id(category_id)
        if category is None:
            raise NotFoundError(f"Category with id={category_id} not found")

        if data.name is not None:
            category.name = data.name
        if data.description is not None:
            category.description = data.description
        if data.image_url is not None:
            category.image_url = data.image_url
        if data.is_active is not None:
            category.is_active = data.is_active

        saved = await self._category_repo.save(category)
        return CategoryResponse.model_validate(saved)

    async def delete(self, category_id: int) -> None:
        category = await self._category_repo.find_by_id(category_id)
        if category is None:
            raise NotFoundError(f"Category with id={category_id} not found")
        await self._category_repo.delete(category)

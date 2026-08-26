"""Product Service."""

from decimal import Decimal
from typing import List, Optional

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate


class ProductService:

    def __init__(
        self,
        product_repo: ProductRepository,
        category_repo: CategoryRepository,
    ):
        self._product_repo = product_repo
        self._category_repo = category_repo

    async def get_all_products(self, skip: int = 0, limit: int = 50) -> List[ProductResponse]:
        products = await self._product_repo.find_all_active(skip=skip, limit=limit)
        return [ProductResponse.from_orm_with_category(p) for p in products]

    async def get_by_id(self, product_id: int) -> ProductResponse:
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product with id={product_id} not found")
        return ProductResponse.from_orm_with_category(product)

    async def search(
        self,
        query: Optional[str] = None,
        category_id: Optional[int] = None,
        brand: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        sort: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ProductResponse]:
        products = await self._product_repo.search(
            query=query,
            category_id=category_id,
            brand=brand,
            min_price=min_price,
            max_price=max_price,
            sort=sort,
            skip=skip,
            limit=limit,
        )
        return [ProductResponse.from_orm_with_category(p) for p in products]

    async def create(self, data: ProductCreate) -> ProductResponse:
        if data.sku and await self._product_repo.exists_by_sku(data.sku):
            raise ConflictError(f"Product with SKU '{data.sku}' already exists")

        if data.category_id:
            category = await self._category_repo.find_by_id(data.category_id)
            if category is None:
                raise NotFoundError(f"Category with id={data.category_id} not found")

        product = Product(
            sku=data.sku,
            name=data.name,
            description=data.description,
            brand=data.brand,
            price=data.price,
            discount_price=data.discount_price,
            stock=data.stock,
            image_url=data.image_url,
            category_id=data.category_id,
            is_active=data.is_active,
            review_count=0,
        )
        saved = await self._product_repo.save(product)
        return ProductResponse.from_orm_with_category(saved)

    async def count_products(self) -> int:
        return await self._product_repo.count_active()

    async def update(self, product_id: int, data: ProductUpdate) -> ProductResponse:
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product with id={product_id} not found")

        if data.category_id is not None:
            category = await self._category_repo.find_by_id(data.category_id)
            if category is None:
                raise NotFoundError(f"Category with id={data.category_id} not found")
            product.category_id = data.category_id

        if data.sku is not None:
            product.sku = data.sku
        if data.name is not None:
            product.name = data.name
        if data.description is not None:
            product.description = data.description
        if data.price is not None:
            product.price = data.price
        if data.discount_price is not None:
            product.discount_price = data.discount_price
        if data.stock is not None:
            product.stock = data.stock
        if data.image_url is not None:
            product.image_url = data.image_url
        if data.is_active is not None:
            product.is_active = data.is_active

        saved = await self._product_repo.save(product)
        return ProductResponse.from_orm_with_category(saved)

    async def soft_delete(self, product_id: int) -> None:
        product = await self._product_repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError(f"Product with id={product_id} not found")
        product.is_active = False
        await self._product_repo.save(product)

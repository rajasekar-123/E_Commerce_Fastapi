"""Unit tests for ProductService."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.services.product_service import ProductService
from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductCreate, ProductUpdate


def make_product(**kwargs) -> Product:
    defaults = dict(
        id=1, sku="SKU001", name="Test Product",
        price=Decimal("100.00"), stock=10, is_active=True,
        review_count=0, category_id=1,
    )
    defaults.update(kwargs)
    p = Product()
    for k, v in defaults.items():
        setattr(p, k, v)
    p.category = Category(id=1, name="Electronics")
    return p


@pytest.mark.asyncio
async def test_get_all_products_returns_active_only(mock_product_repo, mock_category_repo):
    mock_product_repo.find_all_active.return_value = [make_product()]
    service = ProductService(product_repo=mock_product_repo, category_repo=mock_category_repo)

    result = await service.get_all_products()

    assert len(result) == 1
    mock_product_repo.find_all_active.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_id_raises_not_found(mock_product_repo, mock_category_repo):
    mock_product_repo.find_by_id.return_value = None
    service = ProductService(product_repo=mock_product_repo, category_repo=mock_category_repo)

    with pytest.raises(NotFoundError):
        await service.get_by_id(999)


@pytest.mark.asyncio
async def test_soft_delete_sets_is_active_false(mock_product_repo, mock_category_repo):
    """Business rule: delete product sets is_active=False, NOT hard delete."""
    product = make_product()
    mock_product_repo.find_by_id.return_value = product
    mock_product_repo.save.return_value = product
    service = ProductService(product_repo=mock_product_repo, category_repo=mock_category_repo)

    await service.soft_delete(1)

    assert product.is_active is False
    mock_product_repo.save.assert_called_once_with(product)


@pytest.mark.asyncio
async def test_create_raises_conflict_on_duplicate_sku(mock_product_repo, mock_category_repo):
    mock_product_repo.exists_by_sku.return_value = True
    service = ProductService(product_repo=mock_product_repo, category_repo=mock_category_repo)

    with pytest.raises(ConflictError):
        await service.create(ProductCreate(
            sku="DUPLICATE_SKU", name="Test", price=Decimal("10.00"), stock=5, category_id=1
        ))


@pytest.mark.asyncio
async def test_search_delegates_to_repository(mock_product_repo, mock_category_repo):
    mock_product_repo.search.return_value = [make_product()]
    service = ProductService(product_repo=mock_product_repo, category_repo=mock_category_repo)

    result = await service.search(query="test", sort="price_asc")

    mock_product_repo.search.assert_called_once_with(
        query="test", category_id=None, min_price=None, max_price=None, sort="price_asc"
    )
    assert len(result) == 1

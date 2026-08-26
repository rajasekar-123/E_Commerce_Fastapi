"""Product routes — with pagination, brand filter, and search."""

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_product_service
from app.schemas.product import ProductResponse

router = APIRouter()


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List all active products (paginated)",
)
async def get_all_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    product_service=Depends(get_product_service),
) -> List[ProductResponse]:
    return await product_service.get_all_products(skip=skip, limit=limit)


@router.get(
    "/search",
    response_model=List[ProductResponse],
    summary="Search and filter products",
)
async def search_products(
    query: Optional[str] = Query(None, description="Text search in name, description, brand"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price filter"),
    sort: Optional[str] = Query(None, description="Sort: price_asc | price_desc | rating_desc | newest"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    product_service=Depends(get_product_service),
) -> List[ProductResponse]:
    return await product_service.search(
        query=query,
        category_id=category_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
)
async def get_product_by_id(
    product_id: int,
    product_service=Depends(get_product_service),
) -> ProductResponse:
    return await product_service.get_by_id(product_id)

"""Category routes."""

from typing import List
from fastapi import APIRouter, Depends

from app.api.dependencies import get_category_service
from app.schemas.category import CategoryResponse

router = APIRouter()


@router.get(
    "",
    response_model=List[CategoryResponse],
    summary="List all categories",
)
async def get_all_categories(
    category_service=Depends(get_category_service),
) -> List[CategoryResponse]:
    return await category_service.get_all()

"""Router aggregator."""

from fastapi import APIRouter

from app.api.routes.auth_routes import router as auth_router
from app.api.routes.product_routes import router as product_router
from app.api.routes.category_routes import router as category_router
from app.api.routes.order_routes import router as order_router
from app.api.routes.address_routes import router as address_router
from app.api.routes.review_routes import router as review_router
from app.api.routes.payment_routes import router as payment_router
from app.api.routes.admin_routes import router as admin_router
from app.api.routes.ai_routes import router as ai_router
from app.api.routes.document_routes import router as document_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(product_router, prefix="/products", tags=["Products"])
api_router.include_router(category_router, prefix="/categories", tags=["Categories"])
api_router.include_router(order_router, prefix="/orders", tags=["Orders"])
api_router.include_router(address_router, prefix="/users", tags=["Addresses"])
api_router.include_router(review_router, prefix="/products", tags=["Reviews"])
api_router.include_router(payment_router, prefix="/payments", tags=["Payments"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Assistant"])
api_router.include_router(document_router, prefix="/documents", tags=["Documents"])

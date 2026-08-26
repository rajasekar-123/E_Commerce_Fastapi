"""
FastAPI E-Commerce + AI Application Entry Point.

Architecture:
  Presentation (Routes) → Services → Repositories → SQLAlchemy → PostgreSQL
                                  ↓
                            AI Assistant → LLM + RAG + Tools
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown events."""
    # ── Startup ───────────────────────────────────────────────────────────────
    configure_logging(debug=settings.DEBUG)
    logger.info("Starting E-Commerce API", version=settings.APP_VERSION)
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("Shutting down E-Commerce API")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "E-Commerce REST API with AI-powered shopping assistant. "
            "Migrated from Spring Boot to FastAPI with SOLID architecture, "
            "RAG pipeline, and LLM integration."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
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
    from app.api.routes.cart_routes import router as cart_router

    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(product_router, prefix="/products", tags=["Products"])
    app.include_router(category_router, prefix="/categories", tags=["Categories"])
    app.include_router(order_router, prefix="/orders", tags=["Orders"])
    app.include_router(cart_router, prefix="/cart", tags=["Cart"])
    app.include_router(address_router, prefix="/users", tags=["Addresses"])
    app.include_router(review_router, prefix="/products", tags=["Reviews"])
    app.include_router(payment_router, prefix="/payments", tags=["Payments"])
    app.include_router(admin_router, prefix="/admin", tags=["Admin"])
    app.include_router(ai_router, prefix="/ai", tags=["AI Assistant"])
    app.include_router(document_router, prefix="/documents", tags=["Documents"])

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}



    return app

app = create_app()

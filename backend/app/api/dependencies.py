"""
FastAPI dependencies — dependency injection for all services and repositories.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db


# ── Repository dependencies ───────────────────────────────────────────────────

def get_user_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.user_repository import UserRepository
    return UserRepository(db)


def get_product_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.product_repository import ProductRepository
    return ProductRepository(db)


def get_category_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.category_repository import CategoryRepository
    return CategoryRepository(db)


def get_order_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.order_repository import OrderRepository
    return OrderRepository(db)


def get_address_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.address_repository import AddressRepository
    return AddressRepository(db)


def get_review_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.review_repository import ReviewRepository
    return ReviewRepository(db)


def get_cart_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.cart_repository import CartRepository
    return CartRepository(db)


def get_payment_repository(db: AsyncSession = Depends(get_db)):
    from app.repositories.payment_repository import PaymentRepository
    return PaymentRepository(db)


# ── Service dependencies ──────────────────────────────────────────────────────

def get_auth_service(db: AsyncSession = Depends(get_db)):
    from app.services.auth_service import AuthService
    from app.repositories.user_repository import UserRepository
    return AuthService(user_repo=UserRepository(db))


def get_product_service(db: AsyncSession = Depends(get_db)):
    from app.services.product_service import ProductService
    from app.repositories.product_repository import ProductRepository
    from app.repositories.category_repository import CategoryRepository
    return ProductService(
        product_repo=ProductRepository(db),
        category_repo=CategoryRepository(db),
    )


def get_category_service(db: AsyncSession = Depends(get_db)):
    from app.services.category_service import CategoryService
    from app.repositories.category_repository import CategoryRepository
    return CategoryService(category_repo=CategoryRepository(db))


def get_order_service(db: AsyncSession = Depends(get_db)):
    from app.services.order_service import OrderService
    from app.repositories.order_repository import OrderRepository
    from app.repositories.user_repository import UserRepository
    from app.repositories.product_repository import ProductRepository
    from app.repositories.address_repository import AddressRepository
    from app.services.email_service import EmailService
    return OrderService(
        order_repo=OrderRepository(db),
        user_repo=UserRepository(db),
        product_repo=ProductRepository(db),
        address_repo=AddressRepository(db),
        email_service=EmailService(),
        db_session=db,
    )


def get_cart_service(db: AsyncSession = Depends(get_db)):
    from app.services.cart_service import CartService
    from app.repositories.cart_repository import CartRepository
    from app.repositories.product_repository import ProductRepository
    return CartService(
        cart_repo=CartRepository(db),
        product_repo=ProductRepository(db),
    )


def get_address_service(db: AsyncSession = Depends(get_db)):
    from app.services.address_service import AddressService
    from app.repositories.address_repository import AddressRepository
    from app.repositories.user_repository import UserRepository
    return AddressService(
        address_repo=AddressRepository(db),
        user_repo=UserRepository(db),
    )


def get_review_service(db: AsyncSession = Depends(get_db)):
    from app.services.review_service import ReviewService
    from app.repositories.review_repository import ReviewRepository
    from app.repositories.product_repository import ProductRepository
    from app.repositories.user_repository import UserRepository
    return ReviewService(
        review_repo=ReviewRepository(db),
        product_repo=ProductRepository(db),
        user_repo=UserRepository(db),
    )


def get_stripe_service():
    from app.services.stripe_service import StripeService
    return StripeService(
        secret_key=settings.STRIPE_SECRET_KEY,
        webhook_secret=settings.STRIPE_WEBHOOK_SECRET,
    )


def get_payment_service(
    db: AsyncSession = Depends(get_db),
    stripe_svc=Depends(get_stripe_service),
):
    from app.services.payment_service import PaymentService
    from app.repositories.order_repository import OrderRepository
    from app.repositories.payment_repository import PaymentRepository
    return PaymentService(
        order_repo=OrderRepository(db),
        payment_repo=PaymentRepository(db),
        stripe_service=stripe_svc,
    )


# ── AI / LLM dependencies ─────────────────────────────────────────────────────

def get_llm_provider():
    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini":
        from app.ai.llm.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    elif provider == "groq":
        from app.ai.llm.groq_provider import GroqProvider
        return GroqProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
    elif provider == "ollama":
        from app.ai.llm.ollama_provider import OllamaProvider
        return OllamaProvider(base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_MODEL)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def get_embedding_provider():
    provider = settings.EMBEDDING_PROVIDER.lower()
    if provider == "local":
        from app.ai.embeddings.embedding_provider import LocalEmbeddingProvider
        return LocalEmbeddingProvider(model_name=settings.EMBEDDING_MODEL)
    elif provider == "gemini":
        from app.ai.embeddings.embedding_provider import GeminiEmbeddingProvider
        return GeminiEmbeddingProvider(api_key=settings.GEMINI_API_KEY)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


def get_vector_store():
    from app.ai.vectorstore.chroma_store import ChromaVectorStore
    return ChromaVectorStore(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        collection_name=settings.CHROMA_COLLECTION_NAME,
    )


def get_ai_assistant_service(
    db: AsyncSession = Depends(get_db),
    llm=Depends(get_llm_provider),
    embedding=Depends(get_embedding_provider),
    vector_store=Depends(get_vector_store),
):
    from app.ai.services.assistant_service import AssistantService
    from app.ai.services.rag_service import RAGService
    from app.ai.services.tool_service import ToolService
    from app.repositories.product_repository import ProductRepository
    from app.repositories.order_repository import OrderRepository
    from app.repositories.category_repository import CategoryRepository
    from app.repositories.cart_repository import CartRepository

    rag_service = RAGService(
        embedding_provider=embedding,
        vector_store=vector_store,
        llm_provider=llm,
    )
    tool_service = ToolService(
        product_repo=ProductRepository(db),
        order_repo=OrderRepository(db),
        category_repo=CategoryRepository(db),
        cart_repo=CartRepository(db),
    )
    return AssistantService(
        llm_provider=llm,
        rag_service=rag_service,
        tool_service=tool_service,
        redis_url=settings.REDIS_URL,
        chat_ttl=settings.CHAT_HISTORY_TTL_SECONDS,
    )


def get_ingestion_service(
    embedding=Depends(get_embedding_provider),
    vector_store=Depends(get_vector_store),
):
    from app.ai.services.ingestion_service import IngestionService
    return IngestionService(
        embedding_provider=embedding,
        vector_store=vector_store,
        chunk_size=settings.RAG_CHUNK_SIZE,
        chunk_overlap=settings.RAG_CHUNK_OVERLAP,
    )

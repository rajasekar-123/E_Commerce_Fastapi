"""
pytest configuration and shared fixtures.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_product_repo():
    return AsyncMock()


@pytest.fixture
def mock_category_repo():
    return AsyncMock()


@pytest.fixture
def mock_order_repo():
    return AsyncMock()


@pytest.fixture
def mock_address_repo():
    return AsyncMock()


@pytest.fixture
def mock_review_repo():
    return AsyncMock()


@pytest.fixture
def mock_email_service():
    service = MagicMock()
    service.queue_order_confirmation = MagicMock()
    service.send_order_confirmation = AsyncMock()
    return service


@pytest.fixture
def mock_llm_provider():
    provider = AsyncMock()
    provider.generate = AsyncMock(return_value="Test LLM response")
    provider.generate_with_history = AsyncMock(return_value="Test LLM response with history")
    return provider


@pytest.fixture
def mock_embedding_provider():
    provider = AsyncMock()
    provider.embed_query = AsyncMock(return_value=[0.1] * 384)
    provider.embed_documents = AsyncMock(return_value=[[0.1] * 384])
    return provider


@pytest.fixture
def mock_vector_store():
    store = AsyncMock()
    store.similarity_search = AsyncMock(return_value=[])
    store.add_documents = AsyncMock()
    return store

"""Unit tests for AI AssistantService — mocks LLM, RAG, and Tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.services.assistant_service import AssistantService
from app.ai.services.rag_service import RAGService
from app.ai.services.tool_service import ToolService
from app.schemas.ai import ChatRequest, Source


@pytest.fixture
def mock_rag_service(mock_llm_provider, mock_embedding_provider, mock_vector_store):
    return RAGService(
        embedding_provider=mock_embedding_provider,
        vector_store=mock_vector_store,
        llm_provider=mock_llm_provider,
    )


@pytest.fixture
def mock_tool_service():
    service = AsyncMock(spec=ToolService)
    service.search_products.return_value = []
    service.get_user_orders.return_value = []
    return service


@pytest.fixture
def assistant_service(mock_llm_provider, mock_rag_service, mock_tool_service):
    return AssistantService(
        llm_provider=mock_llm_provider,
        rag_service=mock_rag_service,
        tool_service=mock_tool_service,
        redis_url="redis://localhost:6379",
    )


@pytest.mark.asyncio
async def test_chat_returns_response(assistant_service, mock_llm_provider):
    """Basic chat returns a ChatResponse with conversation_id."""
    with patch.object(assistant_service, "_load_history", return_value=[]), \
         patch.object(assistant_service, "_save_history", return_value=None):

        mock_llm_provider.generate_with_history.return_value = "Great question!"
        mock_llm_provider.generate.return_value = ""

        result = await assistant_service.chat(
            request=ChatRequest(message="What products do you have?"),
            user_id=1,
        )

        assert result.answer == "Great question!"
        assert result.conversation_id is not None


@pytest.mark.asyncio
async def test_chat_detects_order_intent(assistant_service, mock_tool_service, mock_llm_provider):
    """Order intent triggers get_user_orders tool."""
    with patch.object(assistant_service, "_load_history", return_value=[]), \
         patch.object(assistant_service, "_save_history", return_value=None):

        mock_llm_provider.generate_with_history.return_value = "Your orders are..."
        mock_llm_provider.generate.return_value = ""

        await assistant_service.chat(
            request=ChatRequest(message="Show me my order status"),
            user_id=42,
        )

        mock_tool_service.get_user_orders.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_chat_detects_product_intent(assistant_service, mock_tool_service, mock_llm_provider):
    """Product search intent triggers search_products tool."""
    with patch.object(assistant_service, "_load_history", return_value=[]), \
         patch.object(assistant_service, "_save_history", return_value=None):

        mock_llm_provider.generate_with_history.return_value = "We have..."
        mock_llm_provider.generate.return_value = ""

        await assistant_service.chat(
            request=ChatRequest(message="find me a laptop under ₹50000"),
            user_id=1,
        )

        mock_tool_service.search_products.assert_called_once()

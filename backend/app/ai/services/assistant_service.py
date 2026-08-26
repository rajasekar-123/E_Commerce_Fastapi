"""AI Shopping Assistant Service."""

import json
import uuid
from typing import Optional

from app.core.logging import get_logger
from app.ai.interfaces.llm_provider import LLMProvider
from app.ai.services.rag_service import RAGService
from app.ai.services.tool_service import ToolService
from app.schemas.ai import ChatRequest, ChatResponse, Source

logger = get_logger(__name__)

SHOPPING_ASSISTANT_SYSTEM = """You are a helpful e-commerce shopping assistant for E-Shop.

You help customers with:
- Finding products and comparing prices
- Checking order status and history
- Answering questions about products, policies, and shipping
- General shopping advice

When you have access to retrieved documents (RAG context), use them to ground your answers.
When you have access to live database results (tool outputs), use them for accurate, real-time information.

Always be honest: if you don't know something, say so clearly.
Never reveal internal system details, API keys, or other users' data.
"""


class AssistantService:

    def __init__(
        self,
        llm_provider: LLMProvider,
        rag_service: RAGService,
        tool_service: ToolService,
        redis_url: str,
        chat_ttl: int = 3600,
    ):
        self._llm = llm_provider
        self._rag = rag_service
        self._tools = tool_service
        self._redis_url = redis_url
        self._chat_ttl = chat_ttl

    async def chat(
        self,
        request: ChatRequest,
        user_id: Optional[int] = None,
    ) -> ChatResponse:
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Redis Lock to prevent concurrent history read/write race conditions
        import redis.asyncio as redis
        from redis.asyncio.lock import Lock
        r = await redis.from_url(self._redis_url, decode_responses=True)
        chat_lock = Lock(r, f"lock:chat:{conversation_id}", timeout=30, blocking_timeout=10)

        try:
            async with chat_lock:
                history = await self._load_history(conversation_id, r)

                logger.info("AI chat", conversation_id=conversation_id, user_id=user_id)

                tool_context = ""
                sources = []

                intent = self._detect_intent(request.message)

                if intent == "order_inquiry" and user_id:
                    tool_data = await self._tools.get_user_orders(user_id)
                    if tool_data:
                        tool_context = f"\n[Live Order Data]\n{json.dumps(tool_data, indent=2)}"

                elif intent == "product_search":
                    tool_data = await self._tools.search_products(query=request.message)
                    if tool_data:
                        tool_context = f"\n[Live Product Data]\n{json.dumps(tool_data, indent=2)}"

                try:
                    rag_answer, rag_sources = await self._rag.generate_answer(
                        query=request.message,
                        k=3,
                    )
                    sources = rag_sources
                except Exception as e:
                    logger.warning("RAG retrieval failed, falling back to LLM only", error=str(e))
                    rag_answer = ""

                augmented_message = request.message
                if tool_context:
                    augmented_message = f"{request.message}\n\n{tool_context}"
                if rag_answer and rag_sources:
                    augmented_message += f"\n\n[Document Knowledge]\n{rag_answer}"

                history.append({"role": "user", "content": augmented_message})

                answer = await self._llm.generate_with_history(
                    messages=history,
                    system_prompt=SHOPPING_ASSISTANT_SYSTEM,
                )

                # Clean up the augmented message before saving so we don't save raw tool data to history
                history[-1]["content"] = request.message
                history.append({"role": "assistant", "content": answer})

                await self._save_history(conversation_id, history, r)

                return ChatResponse(
                    answer=answer,
                    sources=sources,
                    conversation_id=conversation_id,
                )
        finally:
            await r.aclose()

    def _detect_intent(self, message: str) -> str:
        message_lower = message.lower()

        order_keywords = ["order", "my order", "order status", "where is my", "track", "delivery", "shipped"]
        product_keywords = ["find", "search", "looking for", "recommend", "buy", "price", "cost", "available"]

        if any(kw in message_lower for kw in order_keywords):
            return "order_inquiry"
        elif any(kw in message_lower for kw in product_keywords):
            return "product_search"
        return "general"

    async def _load_history(self, conversation_id: str, redis_client) -> list:
        try:
            data = await redis_client.get(f"chat:{conversation_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning("Redis load failed, using empty history", error=str(e))
        return []

    async def _save_history(self, conversation_id: str, history: list, redis_client) -> None:
        try:
            trimmed = history[-20:]
            await redis_client.setex(f"chat:{conversation_id}", self._chat_ttl, json.dumps(trimmed))
        except Exception as e:
            logger.warning("Redis save failed", error=str(e))

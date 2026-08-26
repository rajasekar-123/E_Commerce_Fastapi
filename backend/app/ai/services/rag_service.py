"""RAG Service."""

import json
from typing import List, Optional

from app.core.logging import get_logger
from app.ai.interfaces.embedding_provider import EmbeddingProvider
from app.ai.interfaces.llm_provider import LLMProvider
from app.ai.interfaces.vector_store import Document, IVectorStore
from app.schemas.ai import Source

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful e-commerce shopping assistant for E-Shop.
You have access to product documentation and policies retrieved from our knowledge base.

When answering:
1. Base your answer on the provided context documents
2. If the context does not contain enough information, say so clearly
3. Do NOT make up product details, prices, or policies
4. Be concise and helpful
5. Always cite which document your information comes from

Context documents are provided below."""


class RAGService:

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: IVectorStore,
        llm_provider: LLMProvider,
    ):
        self._embedding = embedding_provider
        self._vector_store = vector_store
        self._llm = llm_provider

    async def retrieve(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[dict] = None,
    ) -> List[Document]:
        logger.info("RAG retrieve", query=query[:100], k=k)
        query_embedding = await self._embedding.embed_query(query)
        documents = await self._vector_store.similarity_search(
            query_embedding=query_embedding,
            k=k,
            filter_metadata=filter_metadata,
        )
        logger.info("RAG retrieved documents", count=len(documents))
        return documents

    def build_context(self, documents: List[Document]) -> str:
        if not documents:
            return "No relevant documents found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            doc_name = doc.metadata.get("document_name", f"Document {i}")
            page = doc.metadata.get("page", "")
            page_str = f" (Page {page})" if page else ""
            context_parts.append(f"[{i}] {doc_name}{page_str}:\n{doc.content}")

        return "\n\n".join(context_parts)

    def build_prompt(self, query: str, context: str) -> str:
        return f"""{SYSTEM_PROMPT}

--- RETRIEVED CONTEXT ---
{context}
--- END CONTEXT ---

User Question: {query}

Answer:"""

    async def generate_answer(
        self,
        query: str,
        filter_metadata: Optional[dict] = None,
        k: int = 5,
    ) -> tuple[str, List[Source]]:
        documents = await self.retrieve(query, k=k, filter_metadata=filter_metadata)
        context = self.build_context(documents)
        prompt = self.build_prompt(query, context)

        logger.info("RAG generating answer", prompt_length=len(prompt))
        answer = await self._llm.generate(prompt)

        sources = []
        for doc in documents:
            if doc.metadata:
                sources.append(
                    Source(
                        document=doc.metadata.get("document_name", "Unknown"),
                        page=doc.metadata.get("page"),
                        relevance_score=doc.relevance_score,
                    )
                )

        return answer, sources

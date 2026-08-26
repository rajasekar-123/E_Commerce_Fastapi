"""
Embedding provider implementations.

Two implementations following Open/Closed Principle:
  - LocalEmbeddingProvider: sentence-transformers (no API key needed)
  - GeminiEmbeddingProvider: Google Gemini Embedding API
"""

import asyncio
from typing import List

from app.domain.interfaces.embedding_provider import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local sentence-transformers embedding provider.
    No API key required. Model downloaded on first use.
    Default model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None  # lazy-loaded

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents in batch (runs in thread pool to avoid blocking)."""
        loop = asyncio.get_event_loop()
        model = self._get_model()
        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(texts, convert_to_list=True)
        )
        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query string."""
        loop = asyncio.get_event_loop()
        model = self._get_model()
        embedding = await loop.run_in_executor(
            None, lambda: model.encode(text, convert_to_list=True)
        )
        return embedding


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini Embedding API provider.
    Uses text-embedding-004 model (768 dimensions).
    """

    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        results = []
        for text in texts:
            embedding = await loop.run_in_executor(
                None,
                lambda t=text: self._genai.embed_content(
                    model="models/text-embedding-004",
                    content=t,
                    task_type="retrieval_document",
                )["embedding"],
            )
            results.append(embedding)
        return results

    async def embed_query(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_query",
            )["embedding"],
        )
        return embedding

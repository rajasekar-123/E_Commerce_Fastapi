"""Embedding provider implementations."""

import asyncio
from typing import List

from app.ai.interfaces.embedding_provider import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        return self._model

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        model = self._get_model()
        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(texts, convert_to_list=True)
        )
        return embeddings

    async def embed_query(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        model = self._get_model()
        embedding = await loop.run_in_executor(
            None, lambda: model.encode(text, convert_to_list=True)
        )
        return embedding


class GeminiEmbeddingProvider(EmbeddingProvider):

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

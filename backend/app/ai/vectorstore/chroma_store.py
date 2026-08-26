"""ChromaDB vector store implementation."""

import uuid
from typing import Any, Dict, List, Optional

import asyncio
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.ai.interfaces.vector_store import Document, IVectorStore


class ChromaVectorStore(IVectorStore):

    def __init__(self, host: str, port: int, collection_name: str):
        self._client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection_name = collection_name
        self._collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_documents(self, documents: List[Document]) -> None:
        if not documents:
            return

        ids = [str(uuid.uuid4()) for _ in documents]
        embeddings = [doc.embedding for doc in documents if doc.embedding is not None]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        await asyncio.to_thread(
            self._collection.add,
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )

    async def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }

        if filter_metadata:
            query_params["where"] = filter_metadata

        results = await asyncio.to_thread(self._collection.query, **query_params)

        documents = []
        if results["documents"] and results["documents"][0]:
            for i, content in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                relevance_score = 1.0 - (distance / 2.0)
                documents.append(
                    Document(
                        content=content,
                        metadata=metadata,
                        relevance_score=relevance_score,
                    )
                )

        return documents

    async def delete_collection(self) -> None:
        await asyncio.to_thread(self._client.delete_collection, self._collection_name)
        self._collection = await asyncio.to_thread(self._get_or_create_collection)

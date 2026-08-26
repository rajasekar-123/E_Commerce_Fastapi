"""Abstract vector store interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Document:
    """A text chunk with associated metadata for RAG."""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    relevance_score: Optional[float] = None


class IVectorStore(ABC):
    """
    Abstract vector store interface.
    Concrete implementation: ChromaVectorStore.
    """

    @abstractmethod
    async def add_documents(self, documents: list[Document]) -> None:
        """Add embedded documents to the vector store."""
        ...

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> list[Document]:
        """
        Find the top-k most similar documents.

        Args:
            query_embedding: The query vector.
            k: Number of results to return.
            filter_metadata: Optional metadata filter (e.g. {"category_id": 10}).

        Returns:
            List of matching Documents with relevance_score set.
        """
        ...

    @abstractmethod
    async def delete_collection(self) -> None:
        """Delete all documents from the collection."""
        ...

"""Abstract vector store interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class Document:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    relevance_score: Optional[float] = None


class IVectorStore(ABC):

    @abstractmethod
    async def add_documents(self, documents: list[Document]) -> None:
        ...

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> list[Document]:
        ...

    @abstractmethod
    async def delete_collection(self) -> None:
        ...

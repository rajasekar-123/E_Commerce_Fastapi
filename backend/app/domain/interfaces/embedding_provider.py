"""Abstract embedding provider interface."""

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """
    Abstract embedding provider interface.
    Kept separate from LLMProvider (Interface Segregation Principle).
    """

    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents for indexing."""
        ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string for similarity search."""
        ...

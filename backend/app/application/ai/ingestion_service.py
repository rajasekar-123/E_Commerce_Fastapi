"""
Document Ingestion Service — processes uploaded files into ChromaDB.

Pipeline:
  File → Extract text → Clean → Chunk → Embed → Store in ChromaDB

Supported file types: PDF, TXT, MD
"""

import io
from pathlib import Path
from typing import List

from app.core.logging import get_logger
from app.domain.interfaces.embedding_provider import EmbeddingProvider
from app.domain.interfaces.vector_store import Document, IVectorStore

logger = get_logger(__name__)


class IngestionService:
    """Single Responsibility: document ingestion and indexing pipeline."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: IVectorStore,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self._embedding = embedding_provider
        self._vector_store = vector_store
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    async def ingest_document(
        self,
        file_content: bytes,
        filename: str,
        metadata: dict | None = None,
    ) -> int:
        """
        Process and index a document into ChromaDB.

        Args:
            file_content: Raw file bytes.
            filename: Original filename (used for metadata and type detection).
            metadata: Optional additional metadata (e.g. category_id, product_id).

        Returns:
            Number of chunks indexed.
        """
        logger.info("Ingesting document", filename=filename)

        # Step 1: Extract text
        text = await self._extract_text(file_content, filename)
        if not text.strip():
            logger.warning("Empty document", filename=filename)
            return 0

        # Step 2: Chunk text
        chunks = self._chunk_text(text)
        logger.info("Text chunked", filename=filename, chunks=len(chunks))

        # Step 3: Build documents with metadata
        base_metadata = {"document_name": filename, **(metadata or {})}
        documents = [
            Document(
                content=chunk,
                metadata={**base_metadata, "chunk_index": i},
            )
            for i, chunk in enumerate(chunks)
        ]

        # Step 4: Generate embeddings
        texts = [doc.content for doc in documents]
        embeddings = await self._embedding.embed_documents(texts)
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding

        # Step 5: Store in ChromaDB
        await self._vector_store.add_documents(documents)
        logger.info("Document ingested successfully", filename=filename, chunks=len(documents))

        return len(documents)

    async def _extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from supported file types."""
        extension = Path(filename).suffix.lower()

        if extension == ".pdf":
            return self._extract_pdf(file_content)
        elif extension in (".txt", ".md"):
            return file_content.decode("utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF using pypdf."""
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(content))
            pages_text = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    pages_text.append(f"[Page {i + 1}]\n{page_text}")
            return "\n\n".join(pages_text)
        except Exception as e:
            logger.error("PDF extraction failed", error=str(e))
            raise ValueError(f"Failed to extract PDF text: {e}")

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        Uses langchain-text-splitters for consistent chunking.
        """
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
            )
            return splitter.split_text(text)
        except ImportError:
            # Fallback: simple fixed-size chunking without overlap
            chunks = []
            for i in range(0, len(text), self._chunk_size - self._chunk_overlap):
                chunks.append(text[i : i + self._chunk_size])
            return chunks

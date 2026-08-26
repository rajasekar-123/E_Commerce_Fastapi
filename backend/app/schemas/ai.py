"""AI Assistant Pydantic schemas."""

from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None  # optional — creates new session if absent


class Source(BaseModel):
    document: str
    page: int | None = None
    relevance_score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []
    conversation_id: str


class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str = "success"
    message: str = ""

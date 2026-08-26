"""Document routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile

from app.core.config import settings
from app.api.dependencies import get_ingestion_service
from app.core.exceptions import BadRequestError
from app.core.security import require_admin
from app.schemas.ai import DocumentUploadResponse
from pathlib import Path

router = APIRouter()


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    dependencies=[Depends(require_admin)],
    summary="Upload and index a document for RAG",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category_id: int | None = Form(None),
    product_id: int | None = Form(None),
    ingestion_service=Depends(get_ingestion_service),
) -> DocumentUploadResponse:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise BadRequestError(
            f"File type '{ext}' not supported. Allowed: {settings.ALLOWED_UPLOAD_EXTENSIONS}"
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise BadRequestError(
            f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    metadata = {}
    if category_id:
        metadata["category_id"] = category_id
    if product_id:
        metadata["product_id"] = product_id

    chunks_created = [0]

    async def ingest():
        chunks_created[0] = await ingestion_service.ingest_document(
            file_content=content,
            filename=file.filename or "document",
            metadata=metadata,
        )

    background_tasks.add_task(ingest)

    return DocumentUploadResponse(
        filename=file.filename or "document",
        chunks_created=0,
        status="processing",
        message="Document is being processed in the background and will be available shortly.",
    )

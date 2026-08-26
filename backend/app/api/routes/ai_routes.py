"""AI Chat routes."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_ai_assistant_service
from app.core.security import get_current_user
from app.schemas.ai import ChatRequest, ChatResponse

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the AI shopping assistant",
)
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    assistant_service=Depends(get_ai_assistant_service),
) -> ChatResponse:
    return await assistant_service.chat(request, user_id=current_user.id)

"""Auth routes."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service
from app.core.security import get_current_user
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from app.schemas.user import UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
    summary="Register a new user account",
)
async def register(
    request: RegisterRequest,
    auth_service=Depends(get_auth_service),
) -> AuthResponse:
    return await auth_service.register(request)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login and receive a JWT token",
)
async def login(
    request: LoginRequest,
    auth_service=Depends(get_auth_service),
) -> AuthResponse:
    return await auth_service.authenticate(request)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)

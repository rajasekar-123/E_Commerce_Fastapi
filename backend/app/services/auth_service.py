"""
Authentication Service.
"""

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest


class AuthService:
    """
    Single Responsibility: handles authentication business logic only.
    Does NOT contain any HTTP/route logic.
    """

    def __init__(self, user_repo: UserRepository):
        self._user_repo = user_repo

    async def register(self, request: RegisterRequest) -> AuthResponse:
        if await self._user_repo.exists_by_email(request.email):
            raise ConflictError("Email address is already in use")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            role=Role.USER,
            is_active=True,
        )
        saved_user = await self._user_repo.save(user)
        token = create_access_token({"sub": saved_user.email, "role": saved_user.role.value})

        return AuthResponse(
            token=token,
            email=saved_user.email,
            role=saved_user.role.value,
            first_name=saved_user.first_name,
            last_name=saved_user.last_name,
        )

    async def authenticate(self, request: LoginRequest) -> AuthResponse:
        user = await self._user_repo.find_by_email(request.email)
        if user is None or not verify_password(request.password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        token = create_access_token({"sub": user.email, "role": user.role.value})
        return AuthResponse(
            token=token,
            email=user.email,
            role=user.role.value,
            first_name=user.first_name,
            last_name=user.last_name,
        )

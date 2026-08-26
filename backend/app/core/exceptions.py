"""
Centralized exception hierarchy and FastAPI exception handlers.

Maps application exceptions → HTTP status codes without exposing internals.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Application Exception Hierarchy ──────────────────────────────────────────


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


class NotFoundError(AppException):
    """Resource not found (404)."""
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppException):
    """Conflict — resource already exists (409)."""
    status_code = 409
    detail = "Resource already exists"


class UnauthorizedError(AppException):
    """Authentication required or invalid credentials (401)."""
    status_code = 401
    detail = "Authentication required"


class ForbiddenError(AppException):
    """Access denied — insufficient permissions (403)."""
    status_code = 403
    detail = "Access denied"


class BadRequestError(AppException):
    """Invalid request data (400)."""
    status_code = 400
    detail = "Bad request"


class InternalError(AppException):
    """Unexpected internal server error (500)."""
    status_code = 500
    detail = "Internal server error"


# ── Error Response Builder ────────────────────────────────────────────────────


def _error_response(status_code: int, detail: Any) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": detail, "status_code": status_code},
    )


# ── Handler Registration ──────────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return _error_response(exc.status_code, exc.detail)

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
        return _error_response(404, "The requested resource was not found")

    @app.exception_handler(405)
    async def method_not_allowed_handler(request: Request, exc: Any) -> JSONResponse:
        return _error_response(405, "Method not allowed")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Never expose stack traces to the client
        import logging
        logging.getLogger(__name__).exception("Unhandled exception: %s", exc)
        return _error_response(500, "An unexpected error occurred")

"""
Centralised exception handling.
FastAPI's default handler returns a generic 500 — we return structured JSON
so clients (and Render logs) get useful info.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class TimezoneAPIError(Exception):
    """Base class for all domain errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidTimezoneError(TimezoneAPIError):
    """Raised when a client-supplied IANA zone is unknown."""

    def __init__(self, tz: str) -> None:
        super().__init__(f"Unknown timezone: '{tz}'", status_code=400)


class InvalidDatetimeError(TimezoneAPIError):
    """Raised when the input datetime cannot be parsed."""

    def __init__(self, raw: str) -> None:
        super().__init__(
            f"Cannot parse datetime '{raw}'. Use ISO-8601 or 'now'.",
            status_code=400,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach our handlers to the FastAPI instance."""

    @app.exception_handler(TimezoneAPIError)
    async def tz_error_handler(_: Request, exc: TimezoneAPIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        # Never leak stack traces in production.
        return JSONResponse(
            status_code=500,
            content={"error": "InternalServerError", "detail": "Unexpected server error."},
        )

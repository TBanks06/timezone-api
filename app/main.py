"""
FastAPI application factory.
This is the file Gunicorn imports: `app.main:app`.
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .config import settings
from .exceptions import register_exception_handlers
from .routes import router


# ---- Logging ---------------------------------------------------------------
def _configure_logging() -> None:
    """Structured, JSON-ish logging suitable for Render's log drain."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force=True,
    )


# ---- Lifespan --------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Runs once at startup and once at shutdown.
    Perfect place for DB pools, caches, warm-up tasks.
    """
    _configure_logging()
    logger = logging.getLogger("timezone-api")
    logger.info(
        "Starting %s v%s (env=%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )
    yield
    logger.info("Shutting down %s", settings.app_name)


# ---- App -------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Convert Nigerian time (Africa/Lagos) to any other timezone.",
    lifespan=lifespan,
    # In production, disable the docs if you want — but leaving them on is
    # useful for internal teams. Gate behind auth in a real public API.
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---- Middleware (order matters — outermost first) --------------------------
# 1. CORS — must be outermost so preflight OPTIONS reaches it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. GZip — compress responses > 1 KB.
app.add_middleware(GZipMiddleware, minimum_size=1000)


# 3. Request-ID + request logging (tiny, in-process, production-safe).
@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    start = time.perf_counter()

    response: Response = await call_next(request)

    elapsed_ms = (time.perf_counter() - start) * 1000
    logging.getLogger("request").info(
        "%s %s -> %s (%.1fms) [rid=%s]",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    return response


# ---- Routes & exception handlers ------------------------------------------
app.include_router(router)
register_exception_handlers(app)

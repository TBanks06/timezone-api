"""
HTTP endpoints. Kept deliberately small — four routes cover every
real use case (info, health, list zones, convert).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from . import converter
from .config import settings
from .converter import convert, parse_input_datetime
from .schemas import (
    ConversionResponse,
    HealthResponse,
    InfoResponse,
    TimezoneListResponse,
)

router = APIRouter()


@router.get("/", response_model=InfoResponse, tags=["meta"])
async def root() -> InfoResponse:
    """Service landing page — also a cheap liveness probe."""
    return InfoResponse(
        name=settings.app_name,
        version=settings.app_version,
        source_timezone=settings.source_timezone,
        endpoints={
            "health": "/health",
            "timezones": "/timezones",
            "convert": "/convert",
        },
    )


@router.get("/health", response_model=HealthResponse, tags=["meta"])
async def health() -> HealthResponse:
    """
    Used by Render's health-check. Returns 200 when the process is
    accepting traffic. Add DB/cache pings here if you ever add them.
    """
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/timezones", response_model=TimezoneListResponse, tags=["timezones"])
async def list_timezones(
    region: str | None = Query(
        None,
        description="Optional IANA region filter, e.g. 'Africa', 'Europe', 'America'.",
        examples=["Africa"],
    ),
) -> TimezoneListResponse:
    """Return every IANA zone the service knows about, with current offset."""
    zones = converter.list_available_timezones(region=region)
    return TimezoneListResponse(count=len(zones), timezones=zones)


@router.get("/convert", response_model=ConversionResponse, tags=["conversion"])
async def convert_time(
    target: str = Query(
        ...,
        description="Target IANA timezone, e.g. 'America/New_York'.",
        examples=["America/New_York"],
    ),
    dt: str = Query(
        "now",
        description="Source datetime in Nigerian time. ISO-8601 or 'now'.",
        examples=["2026-09-13T15:30:00"],
    ),
) -> ConversionResponse:
    """
    Convert a Nigerian time (Africa/Lagos) to another timezone.

    Examples:
      GET /convert?target=America/New_York
      GET /convert?target=Asia/Tokyo&dt=2026-09-13T09:00:00
    """
    from zoneinfo import ZoneInfo

    source_tz = ZoneInfo(settings.source_timezone)
    source_dt = parse_input_datetime(dt, source_tz)
    data = convert(source_dt, target)
    return ConversionResponse(**data)

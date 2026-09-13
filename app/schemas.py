"""
Pydantic models — the contract between the API and its clients.
Using models (instead of raw dicts) gives us:
  • automatic OpenAPI docs
  • input validation
  • a single place to evolve the response shape
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TimeInfo(BaseModel):
    """One side of a conversion (source OR target)."""
    timezone: str = Field(..., examples=["Africa/Lagos"])
    datetime: str = Field(..., examples=["2026-09-13T15:30:00+01:00"])
    utc_offset: str = Field(..., examples=["+01:00"])
    abbreviation: str = Field(..., examples=["WAT"])
    unix_timestamp: int = Field(..., examples=[1757774400])


class ConversionResponse(BaseModel):
    """Returned by GET /convert."""
    source: TimeInfo
    target: TimeInfo
    difference_hours: float = Field(
        ..., description="Target minus source, in hours (signed)."
    )


class TimezoneItem(BaseModel):
    code: str = Field(..., examples=["America/New_York"])
    utc_offset: str = Field(..., examples=["-04:00"])
    current_abbr: str = Field(..., examples=["EDT"])


class TimezoneListResponse(BaseModel):
    count: int
    timezones: list[TimezoneItem]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str


class InfoResponse(BaseModel):
    name: str
    version: str
    source_timezone: str
    endpoints: dict[str, str]

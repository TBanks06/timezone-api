"""
Core domain logic — kept framework-agnostic so it can be unit-tested
without spinning up FastAPI.

We use stdlib `zoneinfo` (PEP 615) instead of `pytz`:
  • no extra dependency
  • uses the OS / `tzdata` package for up-to-date IANA rules
  • correct DST handling out of the box
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import settings
from .exceptions import InvalidDatetimeError, InvalidTimezoneError


def _resolve_zone(name: str) -> ZoneInfo:
    """Return a ZoneInfo or raise InvalidTimezoneError."""
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, KeyError):
        raise InvalidTimezoneError(name)


def parse_input_datetime(raw: str, source_tz: ZoneInfo) -> datetime:
    """
    Accepts:
      • 'now'              -> current time in the source zone
      • ISO-8601 naive     -> interpreted as source-zone local time
      • ISO-8601 aware     -> converted to source zone
    """
    raw = raw.strip()
    if raw.lower() == "now":
        return datetime.now(source_tz)

    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as e:
        raise InvalidDatetimeError(raw) from e

    if dt.tzinfo is None:
        # Treat naive input as source-zone local time.
        return dt.replace(tzinfo=source_tz)

    # Convert aware input into the source zone so all downstream math is consistent.
    return dt.astimezone(source_tz)


def convert(source_dt: datetime, target_zone_name: str) -> dict:
    """
    Convert an already-localised source datetime into the target zone.
    Returns a dict matching ConversionResponse shape.
    """
    target_tz = _resolve_zone(target_zone_name)
    source_tz = source_dt.tzinfo  # must already be set by parse_input_datetime

    target_dt = source_dt.astimezone(target_tz)

    # Offset strings like "+01:00" / "-04:00"
    def _offset(dt: datetime) -> str:
        utcoff = dt.utcoffset()
        if utcoff is None:
            return "+00:00"
        total_seconds = int(utcoff.total_seconds())
        sign = "+" if total_seconds >= 0 else "-"
        h, m = divmod(abs(total_seconds) // 60, 60)
        return f"{sign}{h:02d}:{m:02d}"

    def _abbr(dt: datetime) -> str:
        # strftime %Z gives the abbreviation (e.g. "WAT", "EDT").
        return dt.strftime("%Z") or "UTC"

    source_offset_seconds = source_dt.utcoffset().total_seconds()
    target_offset_seconds = target_dt.utcoffset().total_seconds()
    diff_hours = (target_offset_seconds - source_offset_seconds) / 3600

    return {
        "source": {
            "timezone": str(source_tz),
            "datetime": source_dt.isoformat(),
            "utc_offset": _offset(source_dt),
            "abbreviation": _abbr(source_dt),
            "unix_timestamp": int(source_dt.timestamp()),
        },
        "target": {
            "timezone": str(target_tz),
            "datetime": target_dt.isoformat(),
            "utc_offset": _offset(target_dt),
            "abbreviation": _abbr(target_dt),
            "unix_timestamp": int(target_dt.timestamp()),
        },
        "difference_hours": round(diff_hours, 2),
    }


def list_available_timezones(region: str | None = None) -> list[dict]:
    """
    Return all known IANA zones (optionally filtered by prefix,
    e.g. region='Africa' returns only African zones).
    """
    from zoneinfo import available_timezones

    now_utc = datetime.now(timezone.utc)
    zones = sorted(available_timezones())
    if region:
        prefix = region.strip().title()
        zones = [z for z in zones if z.startswith(f"{prefix}/") or z == prefix]

    result = []
    for z in zones:
        try:
            zi = ZoneInfo(z)
            dt = now_utc.astimezone(zi)
            utcoff = dt.utcoffset()
            total_seconds = int(utcoff.total_seconds()) if utcoff else 0
            sign = "+" if total_seconds >= 0 else "-"
            h, m = divmod(abs(total_seconds) // 60, 60)
            result.append(
                {
                    "code": z,
                    "utc_offset": f"{sign}{h:02d}:{m:02d}",
                    "current_abbr": dt.strftime("%Z") or "UTC",
                }
            )
        except Exception:
            # Skip zones that fail to resolve (defensive).
            continue
    return result

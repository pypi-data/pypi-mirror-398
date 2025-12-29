"""
Datetime operations for utils_devops (datetime_ops module).

Provides timezone-aware helpers, parsing/formatting, arithmetic, boundary and
utility functions. Designed to be stdlib-only (zoneinfo) so it's safe for
minimal environments. Includes __all__ and a `help()` index so IDEs show a
friendly API surface and `help()` output.
"""

from __future__ import annotations

import time
import calendar
import datetime
from typing import Optional, Union
from zoneinfo import ZoneInfo

from .logs import get_library_logger

log = get_library_logger()

__all__ = [
    "DateTimeOpsError",
    "help",
    "current_datetime",
    "current_date",
    "current_time",
    "current_timestamp",
    "parse_datetime",
    "parse_date",
    "parse_time",
    "format_datetime",
    "format_date",
    "format_time",
    "to_iso_datetime",
    "to_iso_date",
    "datetime_to_timestamp",
    "timestamp_to_datetime",
    "change_timezone",
    "utc_to_local",
    "local_to_utc",
    "add_delta",
    "subtract_delta",
    "datetime_diff",
    "human_duration",
    "start_of_day",
    "end_of_day",
    "start_of_week",
    "start_of_month",
    "end_of_month",
    "start_of_year",
    "end_of_year",
    "is_leap_year",
    "is_weekday",
    "is_weekend",
    "days_in_month",
    "sleep",        
    "sleep_until",
]


class DateTimeOpsError(Exception):
    """Custom exception for datetime operations failures."""
    pass


def help() -> None:
    """Print a short index of available functions for interactive use."""
    print(
        """
DevOps Utils — Datetime Operations Module
This module provides timezone-aware helpers, parsing/formatting, arithmetic, boundary and
utility functions. Designed to be stdlib-only (zoneinfo) so it's safe for
minimal environments. Includes __all__ and a `help()` index so IDEs show a
friendly API surface and `help()` output.
Key functions:
DateTimeOpsError: Custom exception for datetime operations failures.
help() -> None: Print a short index of available functions for interactive use.
current_datetime(utc: bool = False) -> datetime.datetime: Return current datetime. When `utc=True` returns timezone-aware UTC.
current_date() -> date: Return current local date.
current_time() -> time: Return current local time (naive).
current_timestamp() -> float: Return current Unix timestamp (seconds since epoch).
parse_datetime(s: str, fmt: Optional[str] = None) -> datetime.datetime: Parse a string into datetime.
parse_date(s: str, fmt: Optional[str] = None) -> date: Parse a string into date.
parse_time(s: str, fmt: Optional[str] = None) -> time: Parse a string into time.
format_datetime(dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str: Format a datetime to string using strftime format.
format_date(d: date, fmt: str = "%Y-%m-%d") -> str: Format a date to string.
format_time(t: time, fmt: str = "%H:%M:%S") -> str: Format a time to string.
to_iso_datetime(dt: datetime.datetime) -> str: Return ISO 8601 representation for datetime.
to_iso_date(d: date) -> str: Return ISO date string.
datetime_to_timestamp(dt: datetime.datetime) -> float: Return Unix timestamp for a datetime (seconds).
timestamp_to_datetime(ts: float, utc: bool = False) -> datetime.datetime: Convert a timestamp (seconds) to datetime. If utc=True returns tz-aware UTC.
change_timezone(dt: datetime.datetime, tz: str) -> datetime.datetime: Change timezone of `dt` to the zone `tz` (IANA name). Returns tz-aware datetime.
utc_to_local(dt: datetime.datetime) -> datetime.datetime: Convert a UTC datetime to local timezone. Accepts naive (treated as UTC) or aware dt.
local_to_utc(dt: datetime.datetime) -> datetime.datetime: Convert a local datetime to UTC. If naive, it's treated as local time.
add_delta(dt: datetime.datetime, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime.datetime: Return dt + timedelta(...)
subtract_delta(dt: datetime.datetime, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime.datetime: Return dt - timedelta(...)
datetime_diff(dt1: datetime.datetime, dt2: datetime.datetime) -> timedelta: Return dt1 - dt2 as timedelta.
human_duration(td: timedelta) -> str: Return human-readable duration like '2 days 3 hours'.
start_of_day(dt: datetime.datetime) -> datetime.datetime: Return dt at 00:00:00.
end_of_day(dt: datetime.datetime) -> datetime.datetime: Return dt at 23:59:59.999999.
start_of_week(dt: datetime.datetime) -> datetime.datetime: Return start (Monday 00:00:00) of the week containing dt.
start_of_month(dt: datetime.datetime) -> datetime.datetime: Return first day of month at 00:00:00.
end_of_month(dt: datetime.datetime) -> datetime.datetime: Return last moment of month containing dt.
start_of_year(dt: datetime.datetime) -> datetime.datetime: Return first day of year at 00:00:00.
end_of_year(dt: datetime.datetime) -> datetime.datetime: Return last moment of year containing dt.
is_leap_year(year: int) -> bool: Return True if `year` is a leap year.
is_weekday(dt: datetime.datetime) -> bool: Return True if dt is Monday-Friday.
is_weekend(dt: datetime.datetime) -> bool: Return True if dt is Saturday or Sunday.
days_in_month(year: int, month: int) -> int: Return number of days in a given month/year.
sleep(seconds: Union[int, float]) -> None: Sleep for the specified number of seconds.
sleep_until(target_time: datetime) -> None: Sleep until the specified datetime.
"""
    )


def sleep(seconds: Union[int, float]) -> None:
    """
    Sleep for the specified number of seconds.
    
    This is a convenience wrapper around time.sleep() that provides
    proper type hints and integrates with the datetime module.
    
    Args:
        seconds: Number of seconds to sleep. Can be integer or float.
    
    Examples:
        >>> sleep(5)          # Sleep for 5 seconds
        >>> sleep(0.5)        # Sleep for 500 milliseconds
        >>> sleep(2.5)        # Sleep for 2.5 seconds
    
    Raises:
        ValueError: If seconds is negative.
    """
    if seconds < 0:
        raise ValueError(f"Cannot sleep for negative time: {seconds} seconds")
    
    time.sleep(seconds)


def sleep_until(target_time: datetime) -> None:
    """
    Sleep until the specified datetime.
    
    Args:
        target_time: The datetime to sleep until.
    
    Raises:
        ValueError: If target_time is in the past.
    """
    now = datetime.now(target_time.tzinfo if target_time.tzinfo else None)
    sleep_seconds = (target_time - now).total_seconds()
    
    if sleep_seconds < 0:
        raise ValueError(f"Target time {target_time} is in the past (current time: {now})")
    
    sleep(sleep_seconds)



# ========================
# Current Time
# ========================


def current_datetime(utc: bool = False) -> datetime.datetime:
    """Return current datetime. When `utc=True` returns timezone-aware UTC.

    When `utc=False` returns naive local datetime (same as datetime.datetime.now()).
    """
    if utc:
        dt = datetime.datetime.now(timezone.utc)
    else:
        dt = datetime.datetime.now()
    log.debug(f"Current datetime (utc={utc}): {dt}")
    return dt


def current_date() -> date:
    """Return current local date."""
    d = date.today()
    log.debug(f"Current date: {d}")
    return d


def current_time() -> time:
    """Return current local time (naive)."""
    t = datetime.datetime.now().time()
    log.debug(f"Current time: {t}")
    return t


def current_timestamp() -> float:
    """Return current Unix timestamp (seconds since epoch)."""
    ts = datetime.datetime.now().timestamp()
    log.debug(f"Current timestamp: {ts}")
    return ts


# ========================
# Parsing
# ========================


def parse_datetime(s: str, fmt: Optional[str] = None) -> datetime.datetime:
    """Parse a string into datetime.

    If `fmt` is provided, uses datetime.strptime(fmt). Otherwise attempts
    fromisoformat() and falls back to common ISO variants.
    """
    try:
        if fmt:
            dt = datetime.datetime.strptime(s, fmt)
        else:
            # prefer fromisoformat which supports offsets
            dt = datetime.datetime.fromisoformat(s)
        log.debug(f"Parsed datetime: {s} -> {dt}")
        return dt
    except Exception as e:
        log.warn(f"Failed to parse datetime '{s}' with fmt '{fmt}': {e}")
        raise DateTimeOpsError(f"Failed to parse datetime '{s}': {e}") from e


def parse_date(s: str, fmt: Optional[str] = None) -> date:
    """Parse a string into date.

    If no fmt provided, uses date.fromisoformat().
    """
    try:
        if fmt:
            d = datetime.datetime.strptime(s, fmt).date()
        else:
            d = date.fromisoformat(s)
        log.debug(f"Parsed date: {s} -> {d}")
        return d
    except Exception as e:
        log.warn(f"Failed to parse date '{s}' with fmt '{fmt}': {e}")
        raise DateTimeOpsError(f"Failed to parse date '{s}': {e}") from e


def parse_time(s: str, fmt: Optional[str] = None) -> time:
    """Parse a string into time.

    If no fmt provided, uses time.fromisoformat().
    """
    try:
        if fmt:
            t = datetime.datetime.strptime(s, fmt).time()
        else:
            t = time.fromisoformat(s)
        log.debug(f"Parsed time: {s} -> {t}")
        return t
    except Exception as e:
        log.warn(f"Failed to parse time '{s}' with fmt '{fmt}': {e}")
        raise DateTimeOpsError(f"Failed to parse time '{s}': {e}") from e


# ========================
# Formatting
# ========================


def format_datetime(dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime to string using strftime format."""
    try:
        s = dt.strftime(fmt)
        log.debug(f"Formatted datetime: {dt} -> {s}")
        return s
    except Exception as e:
        log.error(f"Failed to format datetime {dt} with '{fmt}': {e}")
        raise DateTimeOpsError(f"Failed to format datetime: {e}") from e


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """Format a date to string."""
    try:
        s = d.strftime(fmt)
        log.debug(f"Formatted date: {d} -> {s}")
        return s
    except Exception as e:
        log.error(f"Failed to format date {d} with '{fmt}': {e}")
        raise DateTimeOpsError(f"Failed to format date: {e}") from e


def format_time(t: time, fmt: str = "%H:%M:%S") -> str:
    """Format a time to string."""
    try:
        s = t.strftime(fmt)
        log.debug(f"Formatted time: {t} -> {s}")
        return s
    except Exception as e:
        log.error(f"Failed to format time {t} with '{fmt}': {e}")
        raise DateTimeOpsError(f"Failed to format time: {e}") from e


def to_iso_datetime(dt: datetime.datetime) -> str:
    """Return ISO 8601 representation for datetime."""
    s = dt.isoformat()
    log.debug(f"ISO datetime: {dt} -> {s}")
    return s


def to_iso_date(d: date) -> str:
    """Return ISO date string."""
    s = d.isoformat()
    log.debug(f"ISO date: {d} -> {s}")
    return s


# ========================
# Conversions
# ========================


def datetime_to_timestamp(dt: datetime.datetime) -> float:
    """Return Unix timestamp for a datetime (seconds)."""
    ts = dt.timestamp()
    log.debug(f"Datetime to timestamp: {dt} -> {ts}")
    return ts


def timestamp_to_datetime(ts: float, utc: bool = False) -> datetime.datetime:
    """Convert a timestamp (seconds) to datetime. If utc=True returns tz-aware UTC."""
    if utc:
        dt = datetime.datetime.fromtimestamp(ts, tz=timezone.utc)
    else:
        dt = datetime.datetime.fromtimestamp(ts)
    log.debug(f"Timestamp to datetime (utc={utc}): {ts} -> {dt}")
    return dt


def change_timezone(dt: datetime.datetime, tz: str) -> datetime.datetime:
    """Change timezone of `dt` to the zone `tz` (IANA name). Returns tz-aware datetime."""
    try:
        new_tz = ZoneInfo(tz)
        if dt.tzinfo is None:
            # assume dt is UTC if naive (explicit choice) — caller should provide tz-aware dt
            dt = dt.replace(tzinfo=timezone.utc)
        new_dt = dt.astimezone(new_tz)
        log.debug(f"Changed timezone: {dt} -> {new_dt} ({tz})")
        return new_dt
    except Exception as e:
        log.error(f"Failed to change timezone to '{tz}': {e}")
        raise DateTimeOpsError(f"Failed to change timezone: {e}") from e


def utc_to_local(dt: datetime.datetime) -> datetime.datetime:
    """Convert a UTC datetime to local timezone. Accepts naive (treated as UTC) or aware dt."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local_dt = dt.astimezone()
    log.debug(f"UTC to local: {dt} -> {local_dt}")
    return local_dt


def local_to_utc(dt: datetime.datetime) -> datetime.datetime:
    """Convert a local datetime to UTC. If naive, it's treated as local time.

    Returns a timezone-aware UTC datetime.
    """
    try:
        utc_dt = dt.astimezone(timezone.utc)
        log.debug(f"Local to UTC: {dt} -> {utc_dt}")
        return utc_dt
    except Exception as e:
        # fallback: assume naive is local and call astimezone
        try:
            utc_dt = dt.astimezone(timezone.utc)
            log.debug(f"Local to UTC (fallback): {dt} -> {utc_dt}")
            return utc_dt
        except Exception as e2:
            log.error(f"Failed to convert local to UTC: {e} / {e2}")
            raise DateTimeOpsError(f"Failed to convert local to UTC: {e}") from e


# ========================
# Arithmetic
# ========================


def add_delta(
    dt: datetime.datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
) -> datetime.datetime:
    """Return dt + timedelta(...)"""
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    new_dt = dt + delta
    log.debug(f"Added delta to {dt}: +{delta} -> {new_dt}")
    return new_dt


def subtract_delta(
    dt: datetime.datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
) -> datetime.datetime:
    """Return dt - timedelta(...)"""
    delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    new_dt = dt - delta
    log.debug(f"Subtracted delta from {dt}: -{delta} -> {new_dt}")
    return new_dt


def datetime_diff(dt1: datetime.datetime, dt2: datetime.datetime) -> timedelta:
    """Return dt1 - dt2 as timedelta."""
    diff = dt1 - dt2
    log.debug(f"Datetime diff: {dt1} - {dt2} = {diff}")
    return diff


def human_duration(td: timedelta) -> str:
    """Return human-readable duration like '2 days 3 hours'."""
    total_seconds = int(td.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    s = " ".join(parts) or "0 seconds"
    log.debug(f"Human duration: {td} -> {s}")
    return s


# ========================
# Boundaries
# ========================


def start_of_day(dt: datetime.datetime) -> datetime.datetime:
    """Return dt at 00:00:00."""
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    log.debug(f"Start of day: {dt} -> {start}")
    return start


def end_of_day(dt: datetime.datetime) -> datetime.datetime:
    """Return dt at 23:59:59.999999."""
    end = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    log.debug(f"End of day: {dt} -> {end}")
    return end


def start_of_week(dt: datetime.datetime) -> datetime.datetime:
    """Return start (Monday 00:00:00) of the week containing dt."""
    weekday = dt.weekday()
    start = dt - timedelta(days=weekday)
    start = start_of_day(start)
    log.debug(f"Start of week: {dt} -> {start}")
    return start


def start_of_month(dt: datetime.datetime) -> datetime.datetime:
    """Return first day of month at 00:00:00."""
    start = dt.replace(day=1)
    start = start_of_day(start)
    log.debug(f"Start of month: {dt} -> {start}")
    return start


def end_of_month(dt: datetime.datetime) -> datetime.datetime:
    """Return last moment of month containing dt."""
    # move to the first of next month then subtract a day
    next_month = (dt.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_date = next_month - timedelta(days=1)
    end = end_of_day(end_date)
    log.debug(f"End of month: {dt} -> {end}")
    return end


def start_of_year(dt: datetime.datetime) -> datetime.datetime:
    """Return first day of year at 00:00:00."""
    start = dt.replace(month=1, day=1)
    start = start_of_day(start)
    log.debug(f"Start of year: {dt} -> {start}")
    return start


def end_of_year(dt: datetime.datetime) -> datetime.datetime:
    """Return last moment of year containing dt."""
    end_date = dt.replace(month=12, day=31)
    end = end_of_day(end_date)
    log.debug(f"End of year: {dt} -> {end}")
    return end


# ========================
# Checks
# ========================


def is_leap_year(year: int) -> bool:
    """Return True if `year` is a leap year."""
    leap = calendar.isleap(year)
    log.debug(f"Is leap year {year}: {leap}")
    return leap


def is_weekday(dt: datetime.datetime) -> bool:
    """Return True if dt is Monday-Friday."""
    wd = dt.weekday() < 5
    log.debug(f"Is weekday {dt}: {wd}")
    return wd


def is_weekend(dt: datetime.datetime) -> bool:
    """Return True if dt is Saturday or Sunday."""
    we = dt.weekday() >= 5
    log.debug(f"Is weekend {dt}: {we}")
    return we


def days_in_month(year: int, month: int) -> int:
    """Return number of days in a given month/year."""
    if month == 2 and calendar.isleap(year):
        days = 29
    else:
        days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    log.debug(f"Days in {year}-{month}: {days}")
    return days

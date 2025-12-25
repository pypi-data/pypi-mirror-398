from datetime import date, datetime, timedelta, timezone

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"


def current_datetime() -> datetime:
    """Returns the current datetime"""
    return datetime.utcnow()


def current_date() -> date:
    """Returns the current datetime"""
    return current_datetime().date()


def current_timestamp() -> int:
    """
    Returns the current timestamp from epoch (rounded to the nearest second)
    """
    return int(current_datetime().timestamp())


def _set_uct_timezone(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts


def timestamp_ms(ts: datetime) -> int:
    """
    Return ts timestamp in millisecond (rounded)
    """
    ts_utc = _set_uct_timezone(ts)
    return int(ts_utc.timestamp() * 1000)


def now(tz: bool = False) -> datetime:
    """
    provide current time
    optionally localize timezone
    """
    ts = datetime.utcnow()
    return _set_uct_timezone(ts) if tz else ts


def past_date(past_days: int) -> date:
    """returns a date in the past"""
    return now().date() - timedelta(past_days)


def at_midnight(date_: date) -> datetime:
    """convert date into datetime at midnight: 00:00:00"""
    return datetime.combine(date_, datetime.min.time())


def date_after(day: date, future_days: int) -> date:
    """returns the date `future_days` after `day`"""
    return day + timedelta(future_days)


def format_date(timestamp: datetime | date) -> str:
    return timestamp.strftime(ISO_FORMAT)


def format_rfc_3339_date(timestamp: datetime) -> str:
    return timestamp.isoformat(timespec="seconds") + "Z"


def yesterday() -> date:
    return current_date() - timedelta(days=1)

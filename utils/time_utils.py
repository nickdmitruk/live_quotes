from datetime import datetime, timezone, timedelta

UTC = timezone.utc
UTC_PLUS_3 = timezone(timedelta(hours=3))

def ms_to_dt_utc(ms: int) -> datetime:
    return datetime.fromtimestamp(ms/1000.0, tz=UTC)

def is_weekend_utc3(ms: int) -> bool:
    return ms_to_dt_utc(ms).astimezone(UTC_PLUS_3).weekday() >= 5

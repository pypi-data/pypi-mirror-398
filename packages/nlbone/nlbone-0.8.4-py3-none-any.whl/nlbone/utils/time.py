from datetime import datetime, timedelta, timezone

from dateutil import parser


def now() -> datetime:
    return datetime.now(timezone.utc)


class TimeUtility:
    @classmethod
    def now(cls) -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def minutes_left_from_now(cls, ts: str | datetime) -> int:
        dt = parser.parse(ts) if isinstance(ts, str) else ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta_sec = (dt - now).total_seconds()
        return int(delta_sec // 60)

    @classmethod
    def get_datetime(cls, ts: str | datetime) -> datetime:
        dt = parser.parse(ts) if isinstance(ts, str) else ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    @classmethod
    def get_past_datetime(
        cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    ) -> datetime:
        delta = timedelta(
            days=days,
            seconds=seconds,
            microseconds=microseconds,
            milliseconds=milliseconds,
            minutes=minutes,
            hours=hours,
            weeks=weeks,
        )
        return cls.now() - delta

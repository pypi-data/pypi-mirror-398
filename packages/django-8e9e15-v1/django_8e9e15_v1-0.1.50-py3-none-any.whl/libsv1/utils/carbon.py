from __future__ import annotations
from datetime import datetime, timedelta

class Carbon:

    def __init__(self, date_time: datetime | None = None) -> None:
        self.date_time: datetime = date_time if date_time is not None else datetime.now()

    def __repr__(self) -> str:
        return f"<Carbon({self.date_time.isoformat()})>"

    def __str__(self) -> str:
        return self.format()

    @staticmethod
    def now() -> Carbon:
        return Carbon(datetime.now())

    @staticmethod
    def create(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> Carbon:
        return Carbon(datetime(year, month, day, hour, minute, second))

    @staticmethod
    def parse(date_string: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> Carbon:
        return Carbon(datetime.strptime(date_string, date_format))

    @staticmethod
    def from_timestamp(timestamp: float) -> Carbon:
        return Carbon(datetime.fromtimestamp(timestamp))

    def copy(self) -> Carbon:
        return Carbon(self.date_time)

    def add_days(self, days: int) -> Carbon:
        self.date_time += timedelta(days=days)
        return self

    def add_hours(self, hours: int) -> Carbon:
        self.date_time += timedelta(hours=hours)
        return self

    def add_minutes(self, minutes: int) -> Carbon:
        self.date_time += timedelta(minutes=minutes)
        return self

    def add_seconds(self, seconds: int) -> Carbon:
        self.date_time += timedelta(seconds=seconds)
        return self

    def subtract_days(self, days: int) -> Carbon:
        self.date_time -= timedelta(days=days)
        return self

    def subtract_hours(self, hours: int) -> Carbon:
        self.date_time -= timedelta(hours=hours)
        return self

    def subtract_minutes(self, minutes: int) -> Carbon:
        self.date_time -= timedelta(minutes=minutes)
        return self

    def subtract_seconds(self, seconds: int) -> Carbon:
        self.date_time -= timedelta(seconds=seconds)
        return self

    def format(self, date_format: str = "%Y-%m-%d %H:%M:%S") -> str:
        return self.date_time.strftime(date_format)

    def timestamp(self) -> int:
        return int(self.date_time.timestamp())

    def diff_in_days(self, other: Carbon | datetime) -> int:
        other_dt = other.date_time if isinstance(other, Carbon) else other
        return (self.date_time - other_dt).days

    def diff_in_hours(self, other: Carbon | datetime) -> int:
        other_dt = other.date_time if isinstance(other, Carbon) else other
        return int((self.date_time - other_dt).total_seconds() // 3600)

    def is_past(self) -> bool:
        return self.date_time < datetime.now()

    def is_future(self) -> bool:
        return self.date_time > datetime.now()

    def start_of_day(self) -> Carbon:
        self.date_time = self.date_time.replace(hour=0, minute=0, second=0, microsecond=0)
        return self

    def end_of_day(self) -> Carbon:
        self.date_time = self.date_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        return self

    def to_datetime(self) -> datetime:
        return self.date_time

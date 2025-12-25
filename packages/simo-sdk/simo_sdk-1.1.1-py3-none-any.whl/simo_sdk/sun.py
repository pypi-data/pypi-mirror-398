from __future__ import annotations

import datetime
from zoneinfo import ZoneInfo

from suntime import Sun


class LocalSun(Sun):
    def __init__(self, *, location: str | None, timezone_name: str | None = None):
        lat = 0.0
        lon = 0.0
        if location and isinstance(location, str) and "," in location:
            parts = location.split(",", 1)
            try:
                lat = float(parts[0].strip())
            except Exception:
                lat = 0.0
            try:
                lon = float(parts[1].strip())
            except Exception:
                lon = 0.0
        super().__init__(lat, lon)

        tz = None
        if timezone_name:
            try:
                tz = ZoneInfo(str(timezone_name))
            except Exception:
                tz = None
        self.tz = tz

    def now(self) -> datetime.datetime:
        if self.tz:
            return datetime.datetime.now(tz=self.tz)
        return datetime.datetime.now(datetime.timezone.utc)

    def get_sunrise_time(self, localdatetime: datetime.datetime | None = None):
        sunrise = super().get_sunrise_time(date=localdatetime)
        if not localdatetime or not getattr(localdatetime, "tzinfo", None):
            return sunrise
        return sunrise.astimezone(localdatetime.tzinfo)

    def get_sunset_time(self, localdatetime: datetime.datetime | None = None):
        sunset = super().get_sunset_time(date=localdatetime)
        if not localdatetime or not getattr(localdatetime, "tzinfo", None):
            return sunset
        return sunset.astimezone(localdatetime.tzinfo)

    def is_night(self, localdatetime: datetime.datetime | None = None) -> bool:
        if localdatetime is None:
            localdatetime = self.now()
        if not getattr(localdatetime, "tzinfo", None):
            localdatetime = localdatetime.replace(tzinfo=datetime.timezone.utc)
        utc_dt = localdatetime.astimezone(datetime.timezone.utc)
        if utc_dt > self.get_sunset_time(utc_dt):
            return True
        if utc_dt < self.get_sunrise_time(utc_dt):
            return True
        return False

    def seconds_to_sunset(self, localdatetime: datetime.datetime | None = None) -> float:
        if localdatetime is None:
            localdatetime = self.now()
        if not getattr(localdatetime, "tzinfo", None):
            localdatetime = localdatetime.replace(tzinfo=datetime.timezone.utc)
        utc_dt = localdatetime.astimezone(datetime.timezone.utc)
        return (self.get_sunset_time(utc_dt) - utc_dt).total_seconds()

    def seconds_to_sunrise(self, localdatetime: datetime.datetime | None = None) -> float:
        if localdatetime is None:
            localdatetime = self.now()
        if not getattr(localdatetime, "tzinfo", None):
            localdatetime = localdatetime.replace(tzinfo=datetime.timezone.utc)
        utc_dt = localdatetime.astimezone(datetime.timezone.utc)
        return (self.get_sunrise_time(utc_dt) - utc_dt).total_seconds()

from datetime import datetime, timezone
from typing import Optional
import pytz

time_format = "%Y-%m-%d_%H%M"
date_format = "%Y-%m-%d"


class Time:

    def __init__(
        self,
        UET: Optional[int] = None,
        UTC: Optional[datetime] = None,
        ET: Optional[datetime] = None,
        iso: Optional[str] = None,
        UTC_str: Optional[str] = None,
        ET_str: Optional[str] = None,
        date_str: Optional[str] = None,
    ) -> None:
        if UET is not None:
            self.UET = UET
        elif UTC is not None:
            self.UTC = UTC
        elif ET is not None:
            self.ET = ET
        elif iso is not None:
            self.iso = iso
        elif UTC_str is not None:
            self.UTC_str = UTC_str
        elif ET_str is not None:
            self.ET_str = ET_str
        elif date_str is not None:
            self.date_str = date_str
        else:
            self.UET = int(datetime.now(timezone.utc).timestamp())

    @property
    def UTC(self) -> datetime:
        return datetime.fromtimestamp(self.UET, tz=pytz.utc)

    @UTC.setter
    def UTC(self, value: datetime) -> None:
        self.UET = int(value.timestamp())

    @property
    def ET(self) -> datetime:
        return self.UTC.astimezone(pytz.timezone("US/Eastern"))

    @ET.setter
    def ET(self, value: datetime) -> None:
        self.UET = int(value.timestamp())

    @property
    def iso(self) -> str:
        return datetime.fromtimestamp(self.UET, tz=timezone.utc).isoformat()

    @iso.setter
    def iso(self, value: str) -> None:
        dt = datetime.fromisoformat(value)
        self.UET = int(dt.timestamp())

    @property
    def UTC_str(self) -> str:
        return self.UTC.strftime("%Y-%m-%d_%H%M")

    @UTC_str.setter
    def UTC_str(self, value: str) -> None:
        tz = pytz.timezone("UTC")
        utc = datetime.strptime(value, "%Y-%m-%d_%H%M").astimezone(tz)
        self.UET = int(utc.timestamp())

    @property
    def ET_str(self) -> str:
        return self.ET.strftime("%Y-%m-%d_%H%M")

    @ET_str.setter
    def ET_str(self, value: str) -> None:
        tz = pytz.timezone("US/Eastern")
        et = datetime.strptime(value, "%Y-%m-%d_%H%M").astimezone(tz)
        self.UET = int(et.timestamp())

    @property
    def date_str(self) -> str:
        return self.ET.strftime("%Y-%m-%d")

    @date_str.setter
    def date_str(self, value: str) -> None:
        tz = pytz.timezone("US/Eastern")
        dt = datetime.strptime(value, "%Y-%m-%d")
        dt = tz.localize(dt)
        self.UET = int(dt.timestamp())

    @property
    def ET_disp(self) -> str:
        return self.ET.strftime("%Y-%m-%d %H:%M")

    def __sub__(self, other):
        from ..quantities.time_delta import TimeDelta

        if isinstance(other, Time):
            return Time(UET=self.UET - other.UET)
        if isinstance(other, TimeDelta):
            return Time(UET=self.UET - other.sec)
        if isinstance(other, (float, int)):
            return Time(UET=self.UET - other)
        raise ValueError("'other' must be Time, float, or int.")

    def __rsub__(self, other):
        if isinstance(other, Time):
            return Time(UET=other.UET - self.UET)
        raise ValueError("'other' must be Time.")

    def __add__(self, other):
        from ..quantities.time_delta import TimeDelta

        if isinstance(other, (float, int)):
            return Time(UET=int(self.UET + other))
        if isinstance(other, TimeDelta):
            return Time(UET=self.UET + other.sec)
        if isinstance(other, Time):
            return Time(UET=self.UET + other.UET)
        raise ValueError("'other' must be Time, float, or int.")

    def __radd__(self, other):
        if isinstance(other, Time):
            return Time(UET=other.UET + self.UET)
        raise ValueError("'other' must be Time.")

    def __gt__(self, other):
        if isinstance(other, Time):
            return self.UET > other.UET
        return TypeError("'other' must be an instance of Time.")

    def __rgt__(self, other):
        if isinstance(other, Time):
            return other.UET > self.UET
        return TypeError("'other' must be an instance of Time.")

    def __lt__(self, other):
        if isinstance(other, Time):
            return self.UET < other.UET
        return TypeError("'other' must be an instance of Time.")

    def __rlt__(self, other):
        if isinstance(other, Time):
            return other.UET < self.UET
        return TypeError("'other' must be an instance of Time.")

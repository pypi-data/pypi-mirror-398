"""Time utils"""

from datetime import datetime, timedelta
from typing import Literal, Union
from zoneinfo import ZoneInfo

TIMEZONE = "Asia/Shanghai"


def set_timezone(tz: str = "Asia/Shanghai") -> None:
    global TIMEZONE
    TIMEZONE = tz


class tcdatetime(datetime):
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)
        return instance.replace(tzinfo=ZoneInfo(TIMEZONE))

    @classmethod
    def now(cls):
        return datetime.now(ZoneInfo(TIMEZONE))

    @classmethod
    def fromtimestamp(ts):
        return datetime.fromtimestamp(ts, ZoneInfo(TIMEZONE))

    @classmethod
    def fromisoformat(cls, s):
        return datetime.fromisoformat(s).replace(tzinfo=ZoneInfo(TIMEZONE))

    @classmethod
    def min(cls):
        """NOTE: In datetime, it should be `datetime.min`. However, classmethod property is no longer supported for Python >= 3.13, so use `tcdatetime.min()`."""
        return datetime.min.replace(tzinfo=ZoneInfo(TIMEZONE))

    @classmethod
    def max(cls):
        """NOTE: In datetime, it should be `datetime.max`. However, classmethod property is no longer supported for Python >= 3.13, so use `tcdatetime.max()`."""
        return datetime.max.replace(tzinfo=ZoneInfo(TIMEZONE))


def get_now() -> datetime:
    return datetime.now(ZoneInfo(TIMEZONE))


def get_now_ts() -> int:
    return int(get_now().timestamp())


def get_now_str() -> str:
    return get_now().strftime("%Y-%m-%d %H:%M:%S")


def get_now_ts_str() -> tuple[int, str]:
    now = get_now()
    now_ts = int(now.timestamp())
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    return now_ts, now_str


def get_date_str(date_str: str = None) -> str:
    return date_str or get_now_str()[:10]


def ts_to_str(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def str_to_t(s: str) -> datetime:
    return datetime.fromisoformat(s)


def str_to_ts(s: str) -> int:
    return int(datetime.fromisoformat(s).timestamp())


def t_to_str(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %H:%M:%S")


def t_to_ts(t: datetime) -> int:
    return int(t.timestamp())


def dt_to_sec(dt: timedelta, precision: int = 0) -> float:
    if precision is not None and precision > 0:
        return round(dt.total_seconds(), ndigits=precision)
    else:
        return int(dt.total_seconds())


def dt_to_str(
    dt: Union[timedelta, int, float],
    precision: int = 0,
    str_format: Literal["unit", "colon"] = "colon",
) -> str:
    if isinstance(dt, timedelta):
        hours = dt.days * 24 + dt.seconds // 3600
        minutes = (dt.seconds // 60) % 60
        seconds = dt.seconds % 60
        microseconds = dt.microseconds / 1000000
        precised_seconds = seconds + microseconds
    else:
        hours = int(dt) // 3600
        minutes = (int(dt) // 60) % 60
        seconds = int(dt) % 60
        microseconds = dt - int(dt)
        precised_seconds = seconds + microseconds

    if str_format == "unit":
        hours_str = f"{hours}hr" if hours > 0 else ""
        minutes_str = f"{minutes}min" if minutes > 0 else ""
        if precision is not None and precision > 0:
            seconds_str = f"{precised_seconds:.{precision}f}s"
        else:
            seconds_str = f"{seconds}s"

        time_str = " ".join([hours_str, minutes_str, seconds_str]).strip()
    else:
        hours_str = f"{hours:02d}" if hours > 0 else ""
        minutes_str = f"{minutes:02d}"
        seconds_str = f"{seconds:02d}"
        time_str = ":".join([hours_str, minutes_str, seconds_str]).strip(":")
        if precision is not None and precision > 0:
            time_str += f".{int(microseconds * 10**precision):0{precision}d}"

    return time_str


def unify_ts_and_str(
    t: Union[str, int, None]
) -> tuple[Union[int, None], Union[str, None]]:
    if t is None:
        return None, None
    if isinstance(t, str):
        return str_to_ts(t), t
    if isinstance(t, int):
        return t, ts_to_str(t)
    return t, t

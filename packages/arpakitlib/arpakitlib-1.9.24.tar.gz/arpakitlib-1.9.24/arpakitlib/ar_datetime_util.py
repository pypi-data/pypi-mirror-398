# arpakit

from datetime import datetime, date
from zoneinfo import ZoneInfo

import pytz

from arpakitlib.ar_type_util import raise_for_type


def convert_dt_tz(dt: datetime, tz_info):
    return dt.astimezone(tz_info)


def convert_dt_tz_to_utc(dt: datetime):
    return convert_dt_tz(dt=dt, tz_info=pytz.UTC)


def now_utc_dt() -> datetime:
    return datetime.now(tz=pytz.UTC)


def now_dt(tz=pytz.UTC) -> datetime:
    return datetime.now(tz=tz)


def birth_date_to_age(*, birth_date: date, raise_if_age_negative: bool = False) -> int:
    raise_for_type(birth_date, date)
    now_utc_dt_date = now_utc_dt().date()
    res = now_utc_dt_date.year - birth_date.year
    if (now_utc_dt_date.month, now_utc_dt_date.day) < (birth_date.month, birth_date.day):
        res -= 1
    if raise_if_age_negative and res < 0:
        raise ValueError("raise_if_negative and res < 0")
    return res


def datetime_as_msk_str(datetime_: datetime | None) -> str | None:
    if datetime_ is None:
        return None
    return datetime_.astimezone(ZoneInfo("Europe/Moscow")).strftime("%Y-%m-%d %H:%M:%S %p %Z %z")


def datetime_as_ufa_str(datetime_: datetime | None) -> str | None:
    if datetime_ is None:
        return None
    return datetime_.astimezone(ZoneInfo("Asia/Yekaterinburg")).strftime("%Y-%m-%d %H:%M:%S %p %Z %z")


def __example():
    pass


if __name__ == '__main__':
    __example()

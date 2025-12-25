import datetime


def get_dt_utc_now() -> datetime.datetime:
    # Python devs decided to deprecate datetime.datetime.utcnow() since is naive datetime.
    # https://blog.miguelgrinberg.com/post/it-s-time-for-a-change-datetime-utcnow-is-now-deprecated
    return datetime.datetime.now(tz=datetime.timezone.utc)


def get_utc_today() -> datetime.date:
    return get_dt_utc_now().date()

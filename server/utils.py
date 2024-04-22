import datetime


def round_datetime_to_day(dt: datetime.date, down: bool):
    truncated = dt.replace(hour=0, minute=0, second=0, microsecond=0)

    if down:
        return truncated
    else:
        return truncated + datetime.timedelta(days=1)

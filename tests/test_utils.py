import datetime

from server.utils import round_datetime_to_day


def test_round_datetime_to_day():

    dt = datetime.datetime(2020, 1, 2, 3, 2, 1, 123)

    assert round_datetime_to_day(dt, True) == datetime.datetime(2020, 1, 2, 0, 0, 0, 0)
    assert round_datetime_to_day(dt, False) == datetime.datetime(2020, 1, 3, 0, 0, 0, 0)

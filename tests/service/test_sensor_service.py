import datetime

import pytest

from server.schemas import SensorDataCreateSchema
from server.service import ProcessingResult, SensorService
from server.types import Series, Source


def test_sync_single_site_data(
    httpx_mock, fake_uow, sensor_data_response, sensor_repository
):
    httpx_mock.add_response(json=sensor_data_response)

    SensorService.sync_single_site_data(
        fake_uow, "CLDP0001", 1, Source.breathe_london, Series.pm25, False
    )

    assert len(sensor_repository.data) == 2
    assert type(sensor_repository.data[0]) is SensorDataCreateSchema
    assert sensor_repository.data[0].time == datetime.datetime(2022, 1, 1, 0, 0)
    assert sensor_repository.data[0].value == pytest.approx(28.38500068664551)


def test_get_site_average(fake_uow):
    # Get unenriched data
    result, data = SensorService.get_site_average(
        fake_uow,
        Series.pm25,
        datetime.datetime(2022, 1, 1, 0, 0),
        datetime.datetime(2022, 1, 2, 0, 0),
        False,
    )

    assert result == ProcessingResult.SUCCESS_RETRIEVED
    assert data[0].site_code == "CLDP0001"
    assert data[0].value == pytest.approx(1.23)
    assert data[0].site_details is None

    # Get enriched data
    result, data = SensorService.get_site_average(
        fake_uow,
        Series.pm25,
        datetime.datetime(2022, 1, 1, 0, 0),
        datetime.datetime(2022, 1, 2, 0, 0),
        True,
    )

    assert result == ProcessingResult.SUCCESS_RETRIEVED
    assert data[0].site_code == "CLDP0001"
    assert data[0].value == pytest.approx(1.23)
    assert data[0].site_details is not None


def test_generate_wrapped(fake_uow, sensor_repository):
    result, data = SensorService.generate_wrapped(fake_uow, 2023)

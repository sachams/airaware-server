from datetime import datetime

import pytest

from server.schemas import RangeSchema, SensorDataCreateSchema, SensorDataSchema
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
    assert sensor_repository.data[0].time == datetime(2022, 1, 1, 0, 0)
    assert sensor_repository.data[0].value == pytest.approx(28.38500068664551)


def test_get_site_average(fake_uow):
    # Get unenriched data
    result, data = SensorService.get_site_average(
        fake_uow,
        Series.pm25,
        datetime(2022, 1, 1, 0, 0),
        datetime(2022, 1, 2, 0, 0),
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
        datetime(2022, 1, 1, 0, 0),
        datetime(2022, 1, 2, 0, 0),
        True,
    )

    assert result == ProcessingResult.SUCCESS_RETRIEVED
    assert data[0].site_code == "CLDP0001"
    assert data[0].value == pytest.approx(1.23)
    assert data[0].site_details is not None


def test_generate_wrapped(fake_uow, sensor_repository):
    result, data = SensorService.generate_wrapped(fake_uow, 2023)


def test_get_block_ranges():
    # Create some test ranges
    outliers = {
        "site": [
            # Block 1
            SensorDataSchema(value=0, time=datetime(2022, 1, 1, 0, 0, 0)),
            SensorDataSchema(value=0, time=datetime(2022, 1, 1, 1, 0, 0)),
            SensorDataSchema(value=0, time=datetime(2022, 1, 1, 2, 0, 0)),
            # Block 2
            SensorDataSchema(value=0, time=datetime(2022, 1, 3, 0, 0, 0)),
            SensorDataSchema(value=0, time=datetime(2022, 1, 3, 1, 0, 0)),
            SensorDataSchema(value=0, time=datetime(2022, 1, 3, 2, 0, 0)),
            # Block 3
            SensorDataSchema(value=0, time=datetime(2022, 1, 5, 0, 0, 0)),
            # Block 4
            SensorDataSchema(value=0, time=datetime(2022, 1, 7, 0, 0, 0)),
        ]
    }

    blocks = SensorService.get_block_ranges(outliers)
    assert len(blocks["site"]) == 4

    assert blocks["site"][0] == RangeSchema(
        start=datetime(2022, 1, 1, 0, 0, 0), end=datetime(2022, 1, 1, 2, 0, 0)
    )
    assert blocks["site"][1] == RangeSchema(
        start=datetime(2022, 1, 3, 0, 0, 0), end=datetime(2022, 1, 3, 2, 0, 0)
    )
    assert blocks["site"][2] == RangeSchema(
        start=datetime(2022, 1, 5, 0, 0, 0), end=datetime(2022, 1, 5, 0, 0, 0)
    )
    assert blocks["site"][3] == RangeSchema(
        start=datetime(2022, 1, 7, 0, 0, 0), end=datetime(2022, 1, 7, 0, 0, 0)
    )

import datetime

import pytest

from server.schemas import SensorDataRemoteSchema, SiteCreateSchema
from server.source.breathe_london import BreatheLondon
from server.types import Classification, Series, SiteStatus, Source


def test_name():
    breathe_london = BreatheLondon("dummy_key")
    assert breathe_london.name == Source.breathe_london


def test_get_sites(httpx_mock, site_response):
    httpx_mock.add_response(json=site_response)

    breathe_london = BreatheLondon("app_config.breathe_london_api_key")

    sites = breathe_london.get_sites()

    assert len(sites) == 1
    assert isinstance(sites[0], SiteCreateSchema)

    assert sites[0].site_code == "CLDP0001"
    assert sites[0].name == "Royal London University Hospital"
    assert sites[0].status == SiteStatus.healthy
    assert sites[0].latitude == pytest.approx(51.518775939941406)
    assert sites[0].longitude == pytest.approx(-0.059463899582624435)
    assert sites[0].site_type == Classification.urban_background
    assert sites[0].source == Source.breathe_london
    assert sites[0].is_enabled is True

    assert sites[0].photo_url == "https://api.breathelondon.org/assets/images/CLDP0001.jpg"
    assert sites[0].description == "The Royal London Hospital is home..."
    assert sites[0].start_date == datetime.datetime(2021, 1, 22, 8, 59, 25, 167000)
    assert sites[0].end_date is None
    assert sites[0].borough == "Tower Hamlets"


def test_get_data(httpx_mock, sensor_data_response):
    httpx_mock.add_response(json=sensor_data_response)

    breathe_london = BreatheLondon("dummy_key")

    data = breathe_london.get_sensor_data(
        "CLDP0001",
        datetime.datetime(2022, 1, 1, 0, 0),
        datetime.datetime(2022, 1, 1, 2, 0),
        Series.pm25,
    )

    assert len(data) == 2
    assert isinstance(data[0], SensorDataRemoteSchema)

    assert data[0].time == datetime.datetime(2022, 1, 1, 0, 0)
    assert data[0].value == pytest.approx(28.38500068664551)


def test_get_data_no_data(httpx_mock):
    sample_response = []

    httpx_mock.add_response(json=sample_response)

    breathe_london = BreatheLondon("dummy_key")

    data = breathe_london.get_sensor_data(
        "CLDP0001",
        datetime.datetime(2000, 1, 1, 0, 0),
        datetime.datetime(2000, 1, 2, 0, 0),
        Series.pm25,
    )

    assert len(data) == 0
    assert isinstance(data, list)

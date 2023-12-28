import os
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from main import app, get_unit_of_work
from server.database import SessionLocal
from server.repository.fake_geometry_repository import FakeGeometryRepository
from server.repository.fake_request_repository import FakeRequestRepository
from server.repository.fake_sensor_repository import FakeSensorRepository
from server.unit_of_work.fake_unit_of_work import FakeUnitOfWork


@pytest.fixture()
def session():
    return SessionLocal()


@pytest.fixture()
def request_repository():
    return FakeRequestRepository()


@pytest.fixture()
def sensor_repository():
    return FakeSensorRepository()


@pytest.fixture()
def geometry_repository():
    return FakeGeometryRepository()


@pytest.fixture()
def fake_uow(request_repository, geometry_repository, sensor_repository):
    return FakeUnitOfWork(request_repository, geometry_repository, sensor_repository)


@pytest.fixture()
def get_fake_unit_of_work(fake_uow):
    def get_fake_uow():
        return fake_uow

    return get_fake_uow


@pytest.fixture()
def sensor_data_response():
    return [
        {
            "SiteCode": "CLDP0001",
            "DateTime": "2022-01-01T00:00:00.000Z",
            "DurationNS": 3600000000,
            "ScaledValue": 28.38500068664551,
        },
        {
            "SiteCode": "CLDP0001",
            "DateTime": "2022-01-01T01:00:00.000Z",
            "DurationNS": 3600000000,
            "ScaledValue": 33.7489998626709,
        },
    ]


@pytest.fixture()
def site_response():
    return [
        [
            {
                "SiteCode": "CLDP0001",
                "SiteName": "Royal London University Hospital",
                "Latitude": 51.518775939941406,
                "Longitude": -0.059463899582624435,
                "LocalAuthorityID": None,
                "SiteClassification": "Urban Background",
                "HeadHeight": 2.4000000953674316,
                "ToRoad": 30,
                "SiteLocationType": "Hospital",
                "Indoor": 0,
                "SitePhotoURL": "https://api.breathelondon.org/assets/images/CLDP0001.jpg",
                "SiteDescription": "The Royal London Hospital is home...",
                "SleepTime": 4800,
                "BatteryStatus": "discharging normally",
                "BatteryPercentage": 87,
                "SignalStrength": "4-excellent",
                "SensorsHealthStatus": "OK",
                "OverallStatus": "healthy",
                "DeviceCode": "A7Y9WHYD",
                "StartDate": "2021-01-22T08:59:25.167Z",
                "EndDate": None,
                "LastCommunication": "2023-11-17T05:40:39.380Z",
                "InputPowerError": 0,
                "InputPowerCurrent": 0,
                "InputPowerVoltage": 0,
                "InputBatteryError": 0,
                "InputBatteryVoltage": 3.80599308013916,
                "ChargingStatus": 7,
                "SignalQuality": 31,
                "BatterySleepMultiplier": 16,
                "WeatherError": 0,
                "PMError": 0,
                "NO2Error": 0,
                "LatestINO2Value": None,
                "LatestINO2Index": None,
                "LatestINO2IndexSource": None,
                "LatestIPM10Value": None,
                "LatestIPM10NUMValue": None,
                "LatestIPM1Value": None,
                "LatestIPM1NUMValue": None,
                "LatestIPM25Value": None,
                "LatestIPM25Index": None,
                "LatestIPM25IndexSource": None,
                "LatestIPM25NUMValue": None,
                "LatestRELHUMValue": None,
                "LatestTEMPERATValue": None,
                "SiteActive": 1,
                "SiteGroup": "GLA",
                "PowerTag": "Solar",
                "Enabled": "Y",
                "OtherTags": "Deployed, GLA, Solar300, Tower Hamlets, V1",
                "OrganisationName": "Mayor of London",
                "SponsorName": "Mayor of London",
                "HourlyBulletinEnd": "Nov 16 2023  9:00AM",
            }
        ]
    ]


@pytest.fixture(scope="session")
def client():
    """Returns a FastAPI test client"""
    # Disable the Redis cache when under pytest
    os.environ["ENABLE_CACHE"] = "0"
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="function")
def use_fake_uow(get_fake_unit_of_work):
    """Uses FakeUnitOfWork"""
    app.dependency_overrides[get_unit_of_work] = get_fake_unit_of_work
    yield
    app.dependency_overrides = {}

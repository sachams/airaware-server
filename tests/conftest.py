import datetime
import os
from unittest import mock

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

import app_config
from alembic.command import upgrade
from alembic.config import Config
from main import app, get_unit_of_work
from server.database import SQLALCHEMY_DATABASE_URL, SessionLocal, engine
from server.repository.fake_geometry_repository import FakeGeometryRepository
from server.repository.fake_request_repository import FakeRequestRepository
from server.repository.fake_sensor_repository import FakeSensorRepository
from server.schemas import SensorDataCreateSchema, SiteCreateSchema
from server.types import Classification, Series, SiteStatus, Source
from server.unit_of_work.fake_unit_of_work import FakeUnitOfWork


def run_migrations():

    config = Config(file_="alembic.ini")

    # upgrade the database to the latest revision
    upgrade(config, "head")


@pytest.fixture(scope="session", autouse=True)
def db():
    """Session-wide test database."""

    import pdb

    pdb.set_trace()

    if database_exists(SQLALCHEMY_DATABASE_URL):
        drop_database(SQLALCHEMY_DATABASE_URL)

    create_database(SQLALCHEMY_DATABASE_URL)

    # Apply migrations to the database
    run_migrations()


@pytest.fixture()
def session(db):
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()

    # If the application code calls session.commit, it will end the nested
    # transaction. Need to start a new one when that happens.
    @sa.event.listens_for(session, "after_transaction_end")
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    # Rollback the overall transaction, restoring the state before the test ran.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def dummy_sites():
    return [
        SiteCreateSchema(
            site_code="A123",
            name="Test site 1",
            status=SiteStatus.healthy,
            latitude=50.0,
            longitude=0.01,
            site_type=Classification.urban_background,
            source=Source.breathe_london,
            is_enabled=True,
        ),
        SiteCreateSchema(
            site_code="A456",
            name="Test site 2",
            status=SiteStatus.healthy,
            latitude=50.0,
            longitude=0.01,
            site_type=Classification.urban_background,
            source=Source.breathe_london,
            is_enabled=True,
        ),
    ]


@pytest.fixture
def create_dummy_sparse_data():
    def generate_data_func(sites):
        # Add some dummy data - sparse points
        data = []
        for index, site in enumerate(sites):
            for day in range(1, 3):
                for hour in range(0, 5):
                    data.append(
                        SensorDataCreateSchema(
                            site_id=site.site_id,
                            series=Series.pm25,
                            value=day * hour * (index + 1),
                            time=datetime.datetime(2022, 1, day, hour, 0, 0, 0),
                        )
                    )

        return data

    yield generate_data_func


@pytest.fixture
def create_dummy_heatmap_data():
    def generate_data_func(sites):
        # Add some dummy data - lots of points for heatmap
        data = []
        for index, site in enumerate(sites):
            for day in range(1, 32):
                for hour in range(0, 24):
                    data.append(
                        SensorDataCreateSchema(
                            site_id=site.site_id,
                            series=Series.pm25,
                            value=day * hour * (index + 1),
                            time=datetime.datetime(2023, 1, day, hour, 0, 0, 0),
                        )
                    )

        return data

    yield generate_data_func


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

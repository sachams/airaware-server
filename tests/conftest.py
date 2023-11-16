import pytest
from fastapi.testclient import TestClient
from main import app, get_unit_of_work

from server.repository.fake_geometry_repository import FakeGeometryRepository
from server.repository.fake_request_repository import FakeRequestRepository
from server.repository.fake_sensor_repository import FakeSensorRepository
from server.unit_of_work.fake_unit_of_work import FakeUnitOfWork


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
def get_fake_unit_of_work(request_repository, geometry_repository, sensor_repository):
    def get_fake_uow():
        return FakeUnitOfWork(request_repository, geometry_repository, sensor_repository)

    return get_fake_uow


@pytest.fixture(scope="session")
def client():
    """Returns a FastAPI test client"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def fake_uow(get_fake_unit_of_work):
    """Uses FakeUnitOfWork"""
    app.dependency_overrides[get_unit_of_work] = get_fake_unit_of_work
    yield
    app.dependency_overrides = {}

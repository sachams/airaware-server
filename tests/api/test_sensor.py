from http import HTTPStatus

import pytest
from sqlalchemy.exc import DatabaseError


@pytest.mark.usefixtures("fake_uow")
def test_get_data(client, snapshot):
    response = client.get("/sensor/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00/hour")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("fake_uow")
def test_get_site_average(client, snapshot):
    response = client.get("/site_average/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("fake_uow")
def test_get_sites(client, snapshot):
    response = client.get("/sites")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("fake_uow")
def test_get_site_average_db_exception(client, mocker, sensor_repository):
    sensor_repository.get_site_average = mocker.MagicMock(
        side_effect=DatabaseError(params=None, orig=None, statement="Test exception")
    )

    response = client.get("/site_average/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

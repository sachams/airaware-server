from http import HTTPStatus

import pytest
from sqlalchemy.exc import DatabaseError

from server.types import Classification


@pytest.mark.usefixtures("use_fake_uow")
def test_get_data(client, snapshot):
    response = client.get("/sensor/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00/hour")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("use_fake_uow")
def test_get_data_site_code(client, snapshot):
    response = client.get(
        "/sensor/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00/hour?codes=CLDP0002"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("use_fake_uow")
def test_get_data_type(client, snapshot):
    response = client.get(
        f"/sensor/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00/hour?types={Classification.roadside}"
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("use_fake_uow")
def test_get_site_average(client, snapshot):
    response = client.get("/site_average/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("use_fake_uow")
def test_get_sites(client, snapshot):
    response = client.get("/sites")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == snapshot


@pytest.mark.usefixtures("use_fake_uow")
def test_get_site_average_db_exception(client, mocker, sensor_repository):
    sensor_repository.get_site_average = mocker.MagicMock(
        side_effect=DatabaseError(params=None, orig=None, statement="Test exception")
    )

    response = client.get("/site_average/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

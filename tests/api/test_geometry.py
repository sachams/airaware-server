from http import HTTPStatus

import pytest


@pytest.mark.usefixtures("use_fake_uow")
def test_get_geometry_exists(client):
    response = client.get("/geometry/exists")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"ping": "pong"}


@pytest.mark.usefixtures("use_fake_uow")
def test_get_geometry_doesnt_exist(client):
    response = client.get("/geometry/doesnt_exist")
    assert response.status_code == HTTPStatus.NOT_FOUND

from http import HTTPStatus

import pytest


@pytest.mark.usefixtures("use_fake_uow")
def test_get_healthcheck(client):
    response = client.get("/healthcheck")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}

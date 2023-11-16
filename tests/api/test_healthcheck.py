import pytest
from http import HTTPStatus


@pytest.mark.usefixtures("fake_uow")
def test_get_healthcheck(client):
    response = client.get("/healthcheck")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}

from http import HTTPStatus

import pytest


@pytest.mark.usefixtures("fake_uow")
def test_request_logged(client, request_repository, mocker):
    """Asserts that the request logger works"""

    request_repository.log_request = mocker.MagicMock()

    response = client.get("/sensor/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00/hour")
    assert response.status_code == HTTPStatus.OK
    request_repository.log_request.assert_called_with(
        "http://testserver/sensor/pm25/2022-01-01T10:00:00/2022-02-01T10:00:00/hour",
        "testclient",
    )

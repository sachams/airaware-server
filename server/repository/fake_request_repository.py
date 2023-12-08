from server.repository.abstract_request_repository import AbstractRequestRepository


class FakeRequestRepository(AbstractRequestRepository):
    """A repository that logs API requests"""

    def log_request(self, url: str, ip_address: str):
        pass

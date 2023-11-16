import abc


class AbstractRequestRepository(abc.ABC):
    """A repository that logs API requests"""

    @abc.abstractclassmethod
    def log_request(self, url: str, ip_address: str):
        raise NotImplementedError

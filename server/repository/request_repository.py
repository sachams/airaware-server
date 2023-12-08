import datetime

from sqlalchemy.orm import Session

from server.models.request_log_model import RequestLogModel
from server.repository.abstract_request_repository import AbstractRequestRepository


class RequestRepository(AbstractRequestRepository):
    """A repository that logs API requests"""

    def __init__(self, session: Session):
        self.session = session

    def log_request(self, url: str, ip_address: str):
        """Write an API request to the repository"""
        item = RequestLogModel(path=url, ip_address=ip_address, time=datetime.datetime.utcnow())
        self.session.add(item)

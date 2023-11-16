from server.service.processing_result import ProcessingResult
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork


def log_request(uow: AbstractUnitOfWork, url: str, ip_address: str) -> ProcessingResult:
    with uow:
        item = uow.requests.log_request(url, ip_address)
        uow.commit()

        return ProcessingResult.SUCCESS_CREATED, item

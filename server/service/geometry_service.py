from server.service.processing_result import ProcessingResult
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork


def get_geometry(
    uow: AbstractUnitOfWork,
    name: str,
) -> str:
    with uow:
        geometry = uow.geometries.get_geometry(name)

        if geometry is None:
            return ProcessingResult.ERROR_NOT_FOUND
        else:
            return ProcessingResult.SUCCESS_RETRIEVED, geometry

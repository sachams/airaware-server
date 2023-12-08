import abc
from typing import Any

from server.repository.abstract_geometry_repository import AbstractGeometryRepository
from server.repository.abstract_request_repository import AbstractRequestRepository
from server.repository.abstract_sensor_repository import AbstractSensorRepository


class AbstractUnitOfWork(abc.ABC):
    session = None

    requests: AbstractRequestRepository
    geometries: AbstractGeometryRepository
    sensors: AbstractSensorRepository

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError

    @abc.abstractmethod
    def merge(self, instance, load: bool = True, options: Any | None = None):
        raise NotImplementedError

from typing import Any

from server.database import SessionLocal
from server.repository.geometry_repository import GeometryRepository
from server.repository.request_repository import RequestRepository
from server.repository.sensor_repository import SensorRepository
from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork


class UnitOfWork(AbstractUnitOfWork):
    session = None

    def __enter__(self):
        self.session = SessionLocal()

        self.requests = RequestRepository(self.session)
        self.geometries = GeometryRepository()
        self.sensors = SensorRepository(self.session)

        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        super().__exit__(exc_type, exc_val, exc_tb)

    def commit(self):
        self.session.commit()

    def merge(self, instance, load: bool = True, options: Any | None = None):
        return self.session.merge(instance, load, options)

    def rollback(self):
        self.session.rollback()

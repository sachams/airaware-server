from typing import Any

from server.unit_of_work.abstract_unit_of_work import AbstractUnitOfWork


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self, requests, geometries, sensors):
        self.committed = False
        self.requests = requests
        self.geometries = geometries
        self.sensors = sensors

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass

    def merge(self, instance, load: bool = True, options: Any | None = None):
        pass

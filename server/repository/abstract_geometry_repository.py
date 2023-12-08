import abc


class AbstractGeometryRepository(abc.ABC):
    """A repository that returns named geojson geometries"""

    @abc.abstractmethod
    def get_geometry(self, name: str) -> str:
        raise NotImplementedError
